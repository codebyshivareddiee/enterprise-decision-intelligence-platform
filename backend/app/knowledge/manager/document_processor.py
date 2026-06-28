"""Document processor."""

from app.models.knowledge_asset import KnowledgeAsset, ProcessingMetadata
from app.models.knowledge_schema import KnowledgeSchema
from app.knowledge.models.chunk import PreparedChunk
from app.knowledge.parsers.registry import ParserRegistry
from app.knowledge.interfaces.embedder import DenseEmbedder
from app.knowledge.interfaces.sparse import SparseGenerator
from app.knowledge.exceptions import KnowledgeLayerError

from app.knowledge.analyzer.base import DocumentAnalyzer
from app.knowledge.analyzer.rule_based import RuleBasedAnalyzer
from app.knowledge.analyzer.ai_based import AIDocumentAnalyzer
from app.knowledge.analyzer.models import resolve_chunk_profile
from app.knowledge.chunkers.factory import ChunkingStrategyFactory

class DocumentProcessor:
    """Coordinates parsing, chunking, and embedding of KnowledgeAssets."""

    def __init__(
        self,
        parser_registry: ParserRegistry,
        dense_embedder: DenseEmbedder,
        sparse_generator: SparseGenerator,
        rule_analyzer: DocumentAnalyzer | None = None,
        ai_analyzer: DocumentAnalyzer | None = None,
    ) -> None:
        """Initialize the document processor.
        
        Args:
            parser_registry: Registry to get the right parser for the asset.
            dense_embedder: Embedder to generate dense vectors.
            sparse_generator: Generator to generate sparse vectors.
            rule_analyzer: Optional RuleBasedAnalyzer.
            ai_analyzer: Optional AIDocumentAnalyzer.
        """
        self.parser_registry = parser_registry
        self.dense_embedder = dense_embedder
        self.sparse_generator = sparse_generator
        self.rule_analyzer = rule_analyzer or RuleBasedAnalyzer()
        self.ai_analyzer = ai_analyzer or AIDocumentAnalyzer()

    async def process(
        self, 
        asset: KnowledgeAsset,
        available_schemas: list[KnowledgeSchema]
    ) -> list[PreparedChunk]:
        """Process a KnowledgeAsset into ready-to-index chunks.
        
        Args:
            asset: The KnowledgeAsset to process.
            available_schemas: Schemas available for the analyzer to select from.
            
        Returns:
            A list of PreparedChunk objects containing vectors and metadata.
            
        Raises:
            KnowledgeLayerError: If any step of the process fails.
        """
        try:
            # 1. Parse
            parser = self.parser_registry.get_parser(asset.content_type)
            parsed_doc = await parser.parse(asset)
            
            # 2. Analyze
            analysis_result = await self.rule_analyzer.analyze(asset, parsed_doc, available_schemas)
            
            if not analysis_result or analysis_result.confidence < 0.8:
                ai_result = await self.ai_analyzer.analyze(asset, parsed_doc, available_schemas)
                if ai_result:
                    analysis_result = ai_result
            
            if not analysis_result:
                # Fallback to defaults if both analyzers fail
                from app.knowledge.analyzer.models import DocumentAnalysisResult, ChunkProfile
                analysis_result = DocumentAnalysisResult(
                    matched_schema_id=available_schemas[0].id if available_schemas else None,
                    chunking_strategy="SlidingWindowChunker",
                    chunk_profile=ChunkProfile.MEDIUM,
                    confidence=0.5,
                    reasoning="Fallback strategy.",
                    selection_method="fallback",
                )
                selection_method = "fallback"
            else:
                # Decide if it was rule based or AI based based on which object was returned?
                # For simplicity, if confidence was from rule_analyzer, it's rule_based, else AI
                selection_method = "rule_based" if analysis_result.confidence >= 0.8 and not hasattr(analysis_result, "_from_ai") else "ai"
            
            # Update KnowledgeAsset metadata
            if analysis_result.matched_schema_id:
                asset.schema_id = analysis_result.matched_schema_id
                
            config = resolve_chunk_profile(analysis_result.chunk_profile)
            
            asset.processing_metadata = ProcessingMetadata(
                chunking_strategy=analysis_result.chunking_strategy,
                chunk_profile=analysis_result.chunk_profile.value,
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap,
                selection_method=selection_method,
                reasoning=analysis_result.reasoning,
                confidence=analysis_result.confidence,
                processing_version="1.0.0"
            )
            
            # 3. Chunk
            chunker = ChunkingStrategyFactory.create(analysis_result.chunking_strategy, config)
            chunks = chunker.chunk(parsed_doc.text, asset)
            
            if not chunks:
                return []
                
            chunk_texts = [chunk.content for chunk in chunks]
            
            # 4. Dense Embeddings
            dense_vectors = await self.dense_embedder.embed_chunks(chunk_texts)
            
            # 5. Sparse Vectors
            sparse_vectors = await self.sparse_generator.generate_sparse_chunks(chunk_texts)
            
            # Assemble PreparedChunks
            prepared_chunks = []
            for i, chunk in enumerate(chunks):
                prepared_chunks.append(
                    PreparedChunk(
                        chunk=chunk,
                        dense_vector=dense_vectors[i],
                        sparse_indices=sparse_vectors[i][0],
                        sparse_values=sparse_vectors[i][1],
                    )
                )
                
            return prepared_chunks
        except KnowledgeLayerError:
            raise
        except Exception as e:
            raise KnowledgeLayerError(f"Unexpected error processing asset {asset.id}: {str(e)}") from e
