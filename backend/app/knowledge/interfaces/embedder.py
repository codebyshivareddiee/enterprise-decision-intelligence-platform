"""Dense embedder interface."""

from abc import ABC, abstractmethod

class DenseEmbedder(ABC):
    """Abstract base class for dense embedding generators."""

    @abstractmethod
    async def embed_chunks(self, chunks: list[str]) -> list[list[float]]:
        """Generate dense embeddings for a batch of text chunks.

        Args:
            chunks: A list of text strings.

        Returns:
            A list of embedding vectors (list of floats).

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        pass

    @abstractmethod
    async def embed_query(self, query: str) -> list[float]:
        """Generate a dense embedding for a single search query.

        Args:
            query: The search query text.

        Returns:
            An embedding vector (list of floats).

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        pass
