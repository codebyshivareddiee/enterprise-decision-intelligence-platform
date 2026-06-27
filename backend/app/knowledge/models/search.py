"""Search domain models."""

from uuid import UUID

from pydantic import BaseModel

from app.knowledge.models.chunk import DocumentChunk


class MetadataFilter(BaseModel):
    """Filter criteria for searching the vector store.

    Attributes:
        organization_id: Must match the organization ID of the workspace.
        selected_asset_ids: Only search within these specific assets.
    """

    organization_id: UUID
    selected_asset_ids: list[UUID] | None = None


class SearchResult(BaseModel):
    """A single result from a semantic search.

    Attributes:
        chunk: The retrieved document chunk.
        score: The similarity score from the vector store.
    """

    chunk: DocumentChunk
    score: float
