"""Search service."""

from app.knowledge.interfaces.embedder import DenseEmbedder
from app.knowledge.interfaces.sparse import SparseGenerator
from app.knowledge.interfaces.vector_store import VectorStore
from app.knowledge.models.search import MetadataFilter, SearchResult


class SearchService:
    """Coordinates embedding search queries and retrieving results from the vector store."""

    def __init__(
        self,
        dense_embedder: DenseEmbedder,
        sparse_generator: SparseGenerator,
        vector_store: VectorStore,
    ) -> None:
        """Initialize the search service.

        Args:
            dense_embedder: Embedder for generating dense query vectors.
            sparse_generator: Generator for generating sparse query vectors.
            vector_store: The vector store to search against.
        """
        self.dense_embedder = dense_embedder
        self.sparse_generator = sparse_generator
        self.vector_store = vector_store

    async def search(
        self, query: str, filters: MetadataFilter, top_k: int = 10
    ) -> list[SearchResult]:
        """Perform a hybrid search for the given query.

        Args:
            query: The search text.
            filters: Metadata filters to apply.
            top_k: Number of top results to return.

        Returns:
            A list of SearchResult objects.
        """
        # Generate dense and sparse representations concurrently or sequentially
        # Sequential for simplicity here, but can be gathered
        dense_vector = await self.dense_embedder.embed_query(query)
        sparse_vector = await self.sparse_generator.generate_sparse_query(query)

        return await self.vector_store.search(
            dense_vector=dense_vector,
            sparse_vector=sparse_vector,
            filters=filters,
            top_k=top_k,
        )
