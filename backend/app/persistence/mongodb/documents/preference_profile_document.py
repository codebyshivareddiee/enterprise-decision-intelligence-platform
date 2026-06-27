"""PreferenceProfile MongoDB document schema."""

from __future__ import annotations

from datetime import datetime

from typing_extensions import TypedDict


class PreferenceSignalDocument(TypedDict):
    """Embedded sub-document for a single preference signal."""

    scope: str  # LearningScope enum value
    field_name: str | None
    rule_id: str | None  # UUID as string or None
    description: str
    weight: float
    sample_count: int
    confidence: float


class PreferenceProfileDocument(TypedDict):
    """Raw BSON document stored in the ``preference_profiles`` collection."""

    _id: str  # UUID v4 as string
    organization_id: str
    workspace_id: str
    signals: list[PreferenceSignalDocument]
    total_decisions_processed: int
    last_updated_by_learner_at: str | None  # ISO-8601 string or None
    created_at: datetime
    updated_at: datetime
