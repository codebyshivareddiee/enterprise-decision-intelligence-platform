"""Heading chunker."""

import uuid

from app.knowledge.exceptions import ChunkingError
from app.knowledge.interfaces.chunker import DocumentChunker
from app.knowledge.models.chunk import DocumentChunk
from app.models.knowledge_asset import KnowledgeAsset


class HeadingChunker(DocumentChunker):
    """Splits text by headings (simplified logic for demo)."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str, asset: KnowledgeAsset) -> list[DocumentChunk]:
        if not text:
            return []

        try:
            metadata = {
                "organization_id": str(asset.organization_id),
                "schema_id": str(asset.schema_id),
                "asset_type": asset.content_type.value,
            }
            if asset.lifecycle_state:
                metadata["lifecycle_state"] = asset.lifecycle_state

            chunks: list[DocumentChunk] = []
            lines = text.split("\n")

            current_chunk = []
            chunk_index = 0

            for line in lines:
                # Basic heuristic for a heading
                is_heading = line.strip().isupper() and len(line.strip()) < 60
                if is_heading and current_chunk:
                    # Save previous chunk
                    content = "\n".join(current_chunk).strip()
                    if content:
                        chunks.append(
                            DocumentChunk(
                                chunk_id=str(uuid.uuid4()),
                                asset_id=asset.id,
                                chunk_index=chunk_index,
                                content=content[: self.chunk_size],  # naive size limit
                                metadata=metadata,
                            )
                        )
                        chunk_index += 1
                    current_chunk = []

                current_chunk.append(line)

            if current_chunk:
                content = "\n".join(current_chunk).strip()
                if content:
                    chunks.append(
                        DocumentChunk(
                            chunk_id=str(uuid.uuid4()),
                            asset_id=asset.id,
                            chunk_index=chunk_index,
                            content=content[: self.chunk_size],
                            metadata=metadata,
                        )
                    )

            return chunks
        except Exception as e:
            raise ChunkingError(
                f"Failed to chunk text for asset {asset.id}: {str(e)}"
            ) from e
