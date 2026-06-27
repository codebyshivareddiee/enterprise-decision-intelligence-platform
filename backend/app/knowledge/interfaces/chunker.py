"""Chunker interface."""

from abc import ABC, abstractmethod

from app.knowledge.models.chunk import DocumentChunk
from app.models.knowledge_asset import KnowledgeAsset


class DocumentChunker(ABC):
    """Abstract base class for document chunkers."""

    @abstractmethod
    def chunk(self, text: str, asset: KnowledgeAsset) -> list[DocumentChunk]:
        """Split text into manageable chunks.

        Args:
            text: The full text of the document.
            asset: The parent KnowledgeAsset (for metadata/IDs).

        Returns:
            A list of DocumentChunk objects.

        Raises:
            ChunkingError: If chunking fails.
        """
        pass
