"""Vector store interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.knowledge.models.chunk import PreparedChunk
from app.knowledge.models.search import MetadataFilter, SearchResult


class VectorStore(ABC):
    """Abstract base class for vector store integrations."""

    @abstractmethod
    async def upsert_chunks(self, chunks: list[PreparedChunk]) -> list[str]:
        """Upsert prepared chunks into the vector store.

        Args:
            chunks: A list of PreparedChunk objects containing vectors and metadata.

        Returns:
            A list of vector store point IDs that were upserted.

        Raises:
            VectorStoreError: If the operation fails.
        """
        pass

    @abstractmethod
    async def search(
        self,
        dense_vector: list[float],
        sparse_vector: tuple[list[int], list[float]],
        filters: MetadataFilter,
        top_k: int = 10,
    ) -> list[SearchResult]:
        """Perform a hybrid search in the vector store.

        Args:
            dense_vector: The dense embedding of the query.
            sparse_vector: The sparse vector of the query as (indices, values).
            filters: Metadata filters to apply to the search.
            top_k: Number of results to return.

        Returns:
            A list of SearchResult objects.

        Raises:
            VectorStoreError: If the operation fails.
        """
        pass

    @abstractmethod
    async def delete_by_asset_id(self, asset_id: UUID) -> None:
        """Delete all chunks associated with a specific KnowledgeAsset.

        Args:
            asset_id: The UUID of the KnowledgeAsset.

        Raises:
            VectorStoreError: If the operation fails.
        """
        pass
