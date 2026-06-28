"""Single document chunker."""

import uuid
from app.models.knowledge_asset import KnowledgeAsset
from app.knowledge.interfaces.chunker import DocumentChunker
from app.knowledge.models.chunk import DocumentChunk
from app.knowledge.exceptions import ChunkingError

class SingleDocumentChunker(DocumentChunker):
    """Treats the entire document as a single chunk."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 0) -> None:
        self.chunk_size = chunk_size  # Unused in single document, but kept for signature consistency

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
                
            return [
                DocumentChunk(
                    chunk_id=str(uuid.uuid4()),
                    asset_id=asset.id,
                    chunk_index=0,
                    content=text.strip(),
                    metadata=metadata,
                )
            ]
        except Exception as e:
            raise ChunkingError(f"Failed to chunk text for asset {asset.id}: {str(e)}") from e
