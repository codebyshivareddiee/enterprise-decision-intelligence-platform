"""Sparse generator interface."""

from abc import ABC, abstractmethod

class SparseGenerator(ABC):
    """Abstract base class for sparse vector generators."""

    @abstractmethod
    async def generate_sparse_chunks(self, chunks: list[str]) -> list[tuple[list[int], list[float]]]:
        """Generate sparse vectors for a batch of text chunks.

        Args:
            chunks: A list of text strings.

        Returns:
            A list of tuples containing (indices, values) for the sparse vector.

        Raises:
            SparseGenerationError: If sparse vector generation fails.
        """
        pass

    @abstractmethod
    async def generate_sparse_query(self, query: str) -> tuple[list[int], list[float]]:
        """Generate a sparse vector for a single search query.

        Args:
            query: The search query text.

        Returns:
            A tuple containing (indices, values) for the sparse vector.

        Raises:
            SparseGenerationError: If sparse vector generation fails.
        """
        pass
