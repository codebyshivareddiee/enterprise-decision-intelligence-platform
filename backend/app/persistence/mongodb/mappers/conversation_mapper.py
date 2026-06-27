"""Conversation mapper — Domain ↔ Mongo document."""

from __future__ import annotations

from uuid import UUID

from app.models.conversation import Conversation, ConversationMessage
from app.models.enums import MessageRole
from app.persistence.mongodb.documents.conversation_document import (
    ConversationDocument,
    ConversationMessageDocument,
)


# ---------------------------------------------------------------------------
# ConversationMessage helpers
# ---------------------------------------------------------------------------


def _message_to_document(msg: ConversationMessage) -> ConversationMessageDocument:
    return ConversationMessageDocument(
        role=msg.role.value,
        content=msg.content,
        timestamp=msg.timestamp,
        recommendation_id=(
            str(msg.recommendation_id)
            if msg.recommendation_id is not None
            else None
        ),
    )


def _message_to_domain(doc: ConversationMessageDocument) -> ConversationMessage:
    return ConversationMessage(
        role=MessageRole(doc["role"]),
        content=doc["content"],
        timestamp=doc["timestamp"],
        recommendation_id=(
            UUID(doc["recommendation_id"])
            if doc["recommendation_id"] is not None
            else None
        ),
    )


# ---------------------------------------------------------------------------
# Conversation mapper
# ---------------------------------------------------------------------------


def to_document(conversation: Conversation) -> ConversationDocument:
    """Convert a ``Conversation`` domain model to a Mongo document."""
    return ConversationDocument(
        _id=str(conversation.id),
        organization_id=str(conversation.organization_id),
        workspace_id=str(conversation.workspace_id),
        user_id=str(conversation.user_id),
        title=conversation.title,
        messages=[_message_to_document(m) for m in conversation.messages],
        is_active=conversation.is_active,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def to_domain(doc: ConversationDocument) -> Conversation:
    """Convert a raw Mongo document to a ``Conversation`` domain model."""
    return Conversation(
        id=UUID(doc["_id"]),
        organization_id=UUID(doc["organization_id"]),
        workspace_id=UUID(doc["workspace_id"]),
        user_id=UUID(doc["user_id"]),
        title=doc["title"],
        messages=[_message_to_domain(m) for m in doc["messages"]],
        is_active=doc["is_active"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )
