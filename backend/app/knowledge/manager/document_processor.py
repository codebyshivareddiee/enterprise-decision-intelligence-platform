"""Document processor."""

from app.knowledge.analyzer.ai_based import AIDocumentAnalyzer
from app.knowledge.analyzer.base import DocumentAnalyzer
from app.knowledge.analyzer.models import resolve_chunk_profile
from app.knowledge.analyzer.rule_based import RuleBasedAnalyzer
from app.knowledge.chunkers.factory import ChunkingStrategyFactory
from app.knowledge.exceptions import KnowledgeLayerError
from app.knowledge.interfaces.embedder import DenseEmbedder
from app.knowledge.interfaces.sparse import SparseGenerator
from app.knowledge.models.chunk import PreparedChunk
from app.knowledge.parsers.registry import ParserRegistry
from app.models.knowledge_asset import KnowledgeAsset, ProcessingMetadata
from app.models.knowledge_schema import KnowledgeSchema


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
        self, asset: KnowledgeAsset, available_schemas: list[KnowledgeSchema]
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
            # Order: 1. Schema Defaults, 2. Rule-based, 3. AI override
            analysis_result = None
            selection_method = "unknown"

            # Check schema defaults if a schema is assigned
            schema = next(
                (s for s in available_schemas if s.id == asset.schema_id), None
            )
            if not schema and available_schemas:
                schema = available_schemas[
                    0
                ]  # Fallback to first if none assigned, just for defaults check

            if (
                schema
                and schema.default_chunk_strategy
                and schema.default_chunk_profile
            ):
                from app.knowledge.analyzer.models import (
                    ChunkProfile,
                    DocumentAnalysisResult,
                )

                analysis_result = DocumentAnalysisResult(
                    matched_schema_id=schema.id,
                    chunking_strategy=schema.default_chunk_strategy,
                    chunk_profile=ChunkProfile(schema.default_chunk_profile),
                    confidence=1.0,
                    reasoning="Applied KnowledgeSchema defaults.",
                )
                selection_method = "schema_default"

            if not analysis_result:
                analysis_result = await self.rule_analyzer.analyze(
                    asset, parsed_doc, available_schemas
                )
                if analysis_result and analysis_result.confidence >= 0.8:
                    selection_method = "rule_based"

            if not analysis_result or analysis_result.confidence < 0.8:
                ai_result = await self.ai_analyzer.analyze(
                    asset, parsed_doc, available_schemas
                )
                if ai_result:
                    analysis_result = ai_result
                    selection_method = "ai"

            if not analysis_result:
                # Fallback to defaults if both analyzers fail
                from app.knowledge.analyzer.models import (
                    ChunkProfile,
                    DocumentAnalysisResult,
                )

                analysis_result = DocumentAnalysisResult(
                    matched_schema_id=(
                        available_schemas[0].id if available_schemas else None
                    ),
                    chunking_strategy="SlidingWindowChunker",
                    chunk_profile=ChunkProfile.MEDIUM,
                    confidence=0.5,
                    reasoning="Fallback strategy.",
                )
                selection_method = "fallback"

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
                processing_version="1.0.0",
            )

            # Structured Field Extraction
            if schema and hasattr(self.ai_analyzer, "extract_structured_fields"):
                extracted_metadata = await self.ai_analyzer.extract_structured_fields(
                    asset, parsed_doc, schema
                )
                if extracted_metadata:
                    asset.dynamic_metadata.update(extracted_metadata)

            # 3. Chunk
            chunker = ChunkingStrategyFactory.create(
                analysis_result.chunking_strategy, config
            )
            chunks = chunker.chunk(parsed_doc.text, asset)

            if not chunks:
                return []

            chunk_texts = [chunk.content for chunk in chunks]

            # 4. Dense Embeddings
            dense_vectors = await self.dense_embedder.embed_chunks(chunk_texts)

            # 5. Sparse Vectors
            sparse_vectors = await self.sparse_generator.generate_sparse_chunks(
                chunk_texts
            )

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
            raise KnowledgeLayerError(
                f"Unexpected error processing asset {asset.id}: {str(e)}"
            ) from e

    async def process_batch(
        self,
        assets: list[KnowledgeAsset],
        available_schemas: list[KnowledgeSchema],
        batch_description: str | None = None,
    ) -> list[tuple[KnowledgeAsset, list[PreparedChunk]]]:
        """Process a batch of assets, sampling to determine a common configuration.

        Args:
            assets: List of KnowledgeAssets to process.
            available_schemas: Available schemas for analysis.
            batch_description: Optional human-provided description for the batch.

        Returns:
            List of tuples of (KnowledgeAsset, PreparedChunks).
        """
        if not assets:
            return []

        results = []
        batch_config = None
        selection_method = "unknown"

        # Determine batch config from sample
        max_sample = min(5, len(assets))
        sample_idx = 0

        while sample_idx < max_sample and not batch_config:
            sample_asset = assets[sample_idx]
            parser = self.parser_registry.get_parser(sample_asset.content_type)
            parsed_doc = await parser.parse(sample_asset)

            # Try schema defaults first
            schema = next(
                (s for s in available_schemas if s.id == sample_asset.schema_id), None
            )
            if not schema and available_schemas:
                schema = available_schemas[0]

            if (
                schema
                and schema.default_chunk_strategy
                and schema.default_chunk_profile
            ):
                from app.knowledge.analyzer.models import (
                    ChunkProfile,
                    DocumentAnalysisResult,
                )

                batch_config = DocumentAnalysisResult(
                    matched_schema_id=schema.id,
                    chunking_strategy=schema.default_chunk_strategy,
                    chunk_profile=ChunkProfile(schema.default_chunk_profile),
                    confidence=1.0,
                    reasoning="Applied KnowledgeSchema defaults to batch.",
                )
                selection_method = "schema_default"
                break

            # Then try rule-based
            analysis_result = await self.rule_analyzer.analyze(
                sample_asset, parsed_doc, available_schemas
            )
            if analysis_result and analysis_result.confidence >= 0.8:
                batch_config = analysis_result
                selection_method = "rule_based"
                break

            # Keep sampling if rules aren't confident enough
            sample_idx += 1

        if not batch_config:
            # Fallback to AI analyzer on the first document if no confident rule match found in sample
            sample_asset = assets[0]
            parser = self.parser_registry.get_parser(sample_asset.content_type)
            parsed_doc = await parser.parse(sample_asset)
            batch_config = await self.ai_analyzer.analyze(
                sample_asset, parsed_doc, available_schemas
            )
            selection_method = "ai" if batch_config else "fallback"

        if not batch_config:
            from app.knowledge.analyzer.models import (
                ChunkProfile,
                DocumentAnalysisResult,
            )

            batch_config = DocumentAnalysisResult(
                matched_schema_id=(
                    available_schemas[0].id if available_schemas else None
                ),
                chunking_strategy="SlidingWindowChunker",
                chunk_profile=ChunkProfile.MEDIUM,
                confidence=0.5,
                reasoning="Fallback strategy for batch.",
            )

        # Apply the determined config to all assets, re-analyzing only if structure differs significantly
        # For simplicity, we apply the batch_config to all.
        for asset in assets:
            try:
                # Override process logic inline to avoid re-parsing and re-analyzing
                parser = self.parser_registry.get_parser(asset.content_type)
                parsed_doc = await parser.parse(asset)

                # Update schema if matched
                if batch_config.matched_schema_id:
                    asset.schema_id = batch_config.matched_schema_id

                schema = next(
                    (s for s in available_schemas if s.id == asset.schema_id), None
                )

                config = resolve_chunk_profile(batch_config.chunk_profile)
                asset.processing_metadata = ProcessingMetadata(
                    chunking_strategy=batch_config.chunking_strategy,
                    chunk_profile=batch_config.chunk_profile.value,
                    chunk_size=config.chunk_size,
                    chunk_overlap=config.chunk_overlap,
                    selection_method=selection_method,
                    reasoning=batch_config.reasoning,
                    confidence=batch_config.confidence,
                    processing_version="1.0.0",
                )

                # Structured Field Extraction
                if schema and hasattr(self.ai_analyzer, "extract_structured_fields"):
                    extracted_metadata = (
                        await self.ai_analyzer.extract_structured_fields(
                            asset, parsed_doc, schema
                        )
                    )
                    if extracted_metadata:
                        asset.dynamic_metadata.update(extracted_metadata)

                chunker = ChunkingStrategyFactory.create(
                    batch_config.chunking_strategy, config
                )
                chunks = chunker.chunk(parsed_doc.text, asset)

                if chunks:
                    chunk_texts = [chunk.content for chunk in chunks]
                    dense_vectors = await self.dense_embedder.embed_chunks(chunk_texts)
                    sparse_vectors = await self.sparse_generator.generate_sparse_chunks(
                        chunk_texts
                    )

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
                    results.append((asset, prepared_chunks))
                else:
                    results.append((asset, []))
            except Exception as e:
                # Log error and continue processing the rest of the batch
                asset.processing_error = str(e)
                results.append((asset, []))

        return results
