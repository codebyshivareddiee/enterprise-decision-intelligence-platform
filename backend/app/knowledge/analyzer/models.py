"""Analyzer models."""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ChunkProfile(str, Enum):
    """Predefined chunk profiles."""

    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"
    XLARGE = "XLARGE"


class ChunkingConfig(BaseModel):
    """Configuration derived from a ChunkProfile."""

    chunk_size: int
    chunk_overlap: int


def resolve_chunk_profile(profile: ChunkProfile) -> ChunkingConfig:
    """Resolve a chunk profile to concrete size and overlap."""
    if profile == ChunkProfile.SMALL:
        return ChunkingConfig(chunk_size=400, chunk_overlap=50)
    elif profile == ChunkProfile.MEDIUM:
        return ChunkingConfig(chunk_size=800, chunk_overlap=100)
    elif profile == ChunkProfile.LARGE:
        return ChunkingConfig(chunk_size=1200, chunk_overlap=150)
    elif profile == ChunkProfile.XLARGE:
        return ChunkingConfig(chunk_size=2000, chunk_overlap=200)
    return ChunkingConfig(chunk_size=800, chunk_overlap=100)


class DocumentAnalysisResult(BaseModel):
    """Strongly typed analysis result from Rule-Based or AI Analyzer."""

    matched_schema_id: UUID | None = Field(
        default=None, description="The selected KnowledgeSchema ID."
    )
    chunking_strategy: str = Field(
        ..., description="The selected chunking strategy (e.g. HeadingChunker)."
    )
    chunk_profile: ChunkProfile = Field(..., description="The selected chunk profile.")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0).")
    reasoning: str = Field(..., description="Reasoning for the selection.")
    detected_document_type: str | None = Field(
        default=None, description="Detected type of document."
    )
    detected_language: str | None = Field(
        default=None, description="Detected language."
    )
    estimated_complexity: str | None = Field(
        default=None, description="Estimated complexity (e.g. high, low)."
    )
    requires_human_confirmation: bool = Field(
        default=False, description="Flag if human confirmation is required."
    )
    suggested_lifecycle: list[str] = Field(
        default_factory=list, description="Suggested lifecycle stages."
    )
    suggested_metadata: list[str] = Field(
        default_factory=list, description="Suggested metadata fields."
    )
