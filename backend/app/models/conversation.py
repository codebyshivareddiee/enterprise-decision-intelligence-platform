"""Conversation domain model.

Conversations store the turn-by-turn message history of a user session
within a workspace. They provide conversational context to the AI
agents during a recommendation run.
"""

from uuid import UUID

from pydantic import BaseModel, Field

from app.models.base import AuditedModel
from app.models.enums import MessageRole


class ConversationMessage(BaseModel):
    """A single message turn within a conversation.

    Attributes:
        role: Who authored the message (user, assistant, or system).
        content: The raw text content of the message.
        timestamp: UTC ISO-8601 timestamp of when the message was
            sent. Stored as a string to remain DB-agnostic.
        recommendation_id: If this message is associated with a
            specific recommendation run (e.g., the user reviewed
            results and asked a follow-up), link it here. ``None``
            for general goal-setting messages.
    """

    role: MessageRole = Field(
        ...,
        description="Author role of this message turn.",
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Text content of the message.",
    )
    timestamp: str = Field(
        ...,
        description="UTC ISO-8601 timestamp of when the message was sent.",
    )
    recommendation_id: UUID | None = Field(
        default=None,
        description="Associated recommendation run ID, if applicable.",
    )


class Conversation(AuditedModel):
    """Turn-by-turn message history for a user session within a workspace.

    Conversations provide context to AI agents during goal input and
    recommendation review. The full message list is passed to agents
    that need conversational context.

    A new Conversation is created per user session. Sessions are not
    automatically merged — the AI agent receives the relevant context
    window from the service layer.

    Attributes:
        organization_id: Owning organization — tenant isolation.
        workspace_id: Workspace this conversation is scoped to.
        user_id: The user who initiated and owns this conversation
            session.
        title: Optional human-readable session title or summary, set
            after the first user message. Useful for the UI history
            list.
        messages: Ordered list of message turns. Appended to
            chronologically; never reordered or deleted.
        is_active: Whether this session is still open. Closed sessions
            are preserved for history but no longer receive new
            messages.
    """

    organization_id: UUID = Field(
        ...,
        description="ID of the owning Organization.",
    )
    workspace_id: UUID = Field(
        ...,
        description="ID of the Workspace this conversation is scoped to.",
    )
    user_id: UUID = Field(
        ...,
        description="User ID of the conversation owner.",
    )
    title: str | None = Field(
        default=None,
        max_length=300,
        description="Optional human-readable session title.",
    )
    messages: list[ConversationMessage] = Field(
        default_factory=list,
        description="Ordered message turns. Appended chronologically, never reordered.",
    )
    is_active: bool = Field(
        default=True,
        description="Whether this conversation session is still open.",
    )
