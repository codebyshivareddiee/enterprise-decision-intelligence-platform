"""Shared base model for common audit fields.

All domain entities that are persisted and require identity + timestamp
tracking should inherit from ``AuditedModel``. Entities that are
embedded sub-documents (value objects) should use plain ``BaseModel``
directly.

Keep inheritance minimal — only add to this base what is genuinely
shared by every top-level entity.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


class AuditedModel(BaseModel):
    """Base for top-level domain entities that carry identity and timestamps.

    Attributes:
        id: Universally unique identifier for the entity. Defaults to a
            new UUID v4 generated at instantiation time.
        created_at: UTC timestamp of when the entity was first created.
        updated_at: UTC timestamp of the most recent mutation. Callers
            are responsible for updating this field on every write.
    """

    id: UUID = Field(default_factory=uuid4, description="Unique entity identifier (UUID v4).")
    created_at: datetime = Field(
        default_factory=_utcnow,
        description="UTC timestamp of entity creation.",
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        description="UTC timestamp of the most recent update.",
    )

    model_config = {
        # Allow population by field name (not alias) for convenience.
        "populate_by_name": True,
        # Validate default values so UUID/datetime fields are always correct types.
        "validate_default": True,
    }
