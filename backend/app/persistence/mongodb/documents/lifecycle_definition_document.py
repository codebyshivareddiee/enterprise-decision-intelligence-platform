"""LifecycleDefinition MongoDB document schema."""

from __future__ import annotations

from datetime import datetime

from typing_extensions import TypedDict


class LifecycleStageDocument(TypedDict):
    """Embedded sub-document for a single lifecycle stage."""

    name: str
    description: str | None
    order: int
    is_terminal: bool
    allowed_transitions: list[str]


class LifecycleDefinitionDocument(TypedDict):
    """Raw BSON document stored in the ``lifecycle_definitions`` collection."""

    _id: str                         # UUID v4 as string
    organization_id: str
    name: str
    description: str | None
    stages: list[LifecycleStageDocument]
    created_at: datetime
    updated_at: datetime
