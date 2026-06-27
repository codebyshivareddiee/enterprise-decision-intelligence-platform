"""Document processor."""

from app.models.knowledge_asset import KnowledgeAsset
from app.knowledge.models.chunk import PreparedChunk
from app.knowledge.parsers.registry import ParserRegistry
from app.knowledge.interfaces.chunker import DocumentChunker
from app.knowledge.interfaces.embedder import DenseEmbedder
from app.knowledge.interfaces.sparse import SparseGenerator
from app.knowledge.exceptions import KnowledgeLayerError

class DocumentProcessor:
    """Coordinates parsing, chunking, and embedding of KnowledgeAssets."""

    def __init__(
        self,
        parser_registry: ParserRegistry,
        chunker: DocumentChunker,
        dense_embedder: DenseEmbedder,
        sparse_generator: SparseGenerator,
    ) -> None:
        """Initialize the document processor.
        
        Args:
            parser_registry: Registry to get the right parser for the asset.
            chunker: Chunker to split the text.
            dense_embedder: Embedder to generate dense vectors.
            sparse_generator: Generator to generate sparse vectors.
        """
        self.parser_registry = parser_registry
        self.chunker = chunker
        self.dense_embedder = dense_embedder
        self.sparse_generator = sparse_generator

    async def process(self, asset: KnowledgeAsset) -> list[PreparedChunk]:
        """Process a KnowledgeAsset into ready-to-index chunks.
        
        Steps:
        1. Parse the document to extract text.
        2. Chunk the text.
        3. Generate dense embeddings for chunks.
        4. Generate sparse vectors for chunks.
        
        Args:
            asset: The KnowledgeAsset to process.
            
        Returns:
            A list of PreparedChunk objects containing vectors and metadata.
            
        Raises:
            KnowledgeLayerError: If any step of the process fails.
        """
        try:
            # 1. Parse
            parser = self.parser_registry.get_parser(asset.content_type)
            text = await parser.parse(asset)
            
            # 2. Chunk
            chunks = self.chunker.chunk(text, asset)
            if not chunks:
                return []
                
            chunk_texts = [chunk.content for chunk in chunks]
            
            # 3. Dense Embeddings
            dense_vectors = await self.dense_embedder.embed_chunks(chunk_texts)
            
            # 4. Sparse Vectors
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
