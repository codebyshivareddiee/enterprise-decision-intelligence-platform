"""Conversation MongoDB document schema."""

from __future__ import annotations

from datetime import datetime

from typing_extensions import TypedDict


class ConversationMessageDocument(TypedDict):
    """Embedded sub-document for a single conversation message turn."""

    role: str  # MessageRole enum value
    content: str
    timestamp: str  # ISO-8601 string
    recommendation_id: str | None  # UUID as string or None


class ConversationDocument(TypedDict):
    """Raw BSON document stored in the ``conversations`` collection."""

    _id: str  # UUID v4 as string
    organization_id: str
    workspace_id: str
    user_id: str  # UUID as string
    title: str | None
    messages: list[ConversationMessageDocument]
    is_active: bool
    created_at: datetime
    updated_at: datetime
