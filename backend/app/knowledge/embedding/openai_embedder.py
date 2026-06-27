"""OpenAI dense embedder implementation."""

from openai import AsyncOpenAI
from app.knowledge.interfaces.embedder import DenseEmbedder
from app.knowledge.exceptions import EmbeddingError

class OpenAIEmbedder(DenseEmbedder):
    """Dense embedder using OpenAI's text-embedding models."""

    def __init__(self, client: AsyncOpenAI | None = None, model: str = "text-embedding-3-small") -> None:
        """Initialize the OpenAI embedder.
        
        Args:
            client: An optional AsyncOpenAI client. If None, it will be instantiated.
            model: The OpenAI embedding model to use.
        """
        self.client = client or AsyncOpenAI()
        self.model = model

    async def embed_chunks(self, chunks: list[str]) -> list[list[float]]:
        """Generate dense embeddings for a batch of text chunks.

        Args:
            chunks: A list of text strings.

        Returns:
            A list of embedding vectors.

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        if not chunks:
            return []
            
        try:
            response = await self.client.embeddings.create(
                input=chunks,
                model=self.model
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            raise EmbeddingError(f"Failed to embed {len(chunks)} chunks using {self.model}: {str(e)}") from e

    async def embed_query(self, query: str) -> list[float]:
        """Generate a dense embedding for a single search query.

        Args:
            query: The search query text.

        Returns:
            An embedding vector.

        Raises:
            EmbeddingError: If embedding generation fails.
        """
        try:
            response = await self.client.embeddings.create(
                input=[query],
                model=self.model
            )
            return response.data[0].embedding
        except Exception as e:
            raise EmbeddingError(f"Failed to embed query using {self.model}: {str(e)}") from e
