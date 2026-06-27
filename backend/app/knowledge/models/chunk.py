"""Chunk domain models."""

from uuid import UUID
from pydantic import BaseModel, Field

class DocumentChunk(BaseModel):
    """Represents a text chunk of a KnowledgeAsset.

    Attributes:
        chunk_id: Unique identifier for this chunk (used as Qdrant point ID).
        asset_id: The ID of the parent KnowledgeAsset.
        chunk_index: The sequential index of this chunk within the document.
        content: The actual text content of the chunk.
        metadata: Additional metadata for filtering (organization_id, etc.).
    """
    chunk_id: str = Field(..., description="Unique ID for this chunk (UUID string).")
    asset_id: UUID = Field(..., description="ID of the parent KnowledgeAsset.")
    chunk_index: int = Field(..., description="Sequential index of the chunk.")
    content: str = Field(..., description="Text content of the chunk.")
    metadata: dict[str, object] = Field(default_factory=dict, description="Metadata for filtering.")

class PreparedChunk(BaseModel):
    """A chunk that has been fully processed (dense and sparse vectors generated) and is ready for indexing."""
    chunk: DocumentChunk
    dense_vector: list[float]
    sparse_indices: list[int]
    sparse_values: list[float]
