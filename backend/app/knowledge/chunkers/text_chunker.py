"""Text chunker implementation."""

import uuid
from typing import Any

from app.knowledge.exceptions import ChunkingError
from app.knowledge.interfaces.chunker import DocumentChunker
from app.knowledge.models.chunk import DocumentChunk
from app.models.knowledge_asset import KnowledgeAsset


class TextChunker(DocumentChunker):
    """Splits text into chunks of a specific size with overlap."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150) -> None:
        """Initialize the text chunker.

        Args:
            chunk_size: Maximum characters per chunk.
            chunk_overlap: Number of characters to overlap between chunks.
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive.")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size.")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str, asset: KnowledgeAsset) -> list[DocumentChunk]:
        """Split text into manageable chunks.

        Args:
            text: The full text of the document.
            asset: The parent KnowledgeAsset.

        Returns:
            A list of DocumentChunk objects.

        Raises:
            ChunkingError: If chunking fails.
        """
        if not text:
            return []

        try:
            chunks: list[DocumentChunk] = []
            start = 0
            text_length = len(text)
            chunk_index = 0

            while start < text_length:
                end = start + self.chunk_size

                # If we're not at the end of the text, try to find a nice break point (e.g. newline or space)
                # For simplicity in this demo, we just do a hard slice.
                # A more advanced chunker would look for the last space/newline before `end`.

                chunk_text = text[start:end].strip()
                if chunk_text:
                    metadata: dict[str, Any] = {
                        "organization_id": str(asset.organization_id),
                        "schema_id": str(asset.schema_id),
                        "asset_type": asset.content_type.value,
                    }

                    if asset.lifecycle_state:
                        metadata["lifecycle_state"] = asset.lifecycle_state

                    chunks.append(
                        DocumentChunk(
                            chunk_id=str(uuid.uuid4()),
                            asset_id=asset.id,
                            chunk_index=chunk_index,
                            content=chunk_text,
                            metadata=metadata,
                        )
                    )
                    chunk_index += 1

                if end >= text_length:
                    break

                start += self.chunk_size - self.chunk_overlap

            return chunks
        except Exception as e:
            raise ChunkingError(
                f"Failed to chunk text for asset {asset.id}: {str(e)}"
            ) from e
