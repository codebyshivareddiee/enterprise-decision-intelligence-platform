"""KnowledgeSchema MongoDB document schema."""

from __future__ import annotations

from datetime import datetime

from typing_extensions import TypedDict


class SchemaFieldDocument(TypedDict):
    """Embedded sub-document for a single schema field."""

    name: str
    label: str
    field_type: str           # FieldType enum value
    required: bool
    description: str | None
    allowed_values: list[str] | None


class LifecycleDefinitionDocument(TypedDict):
    """Embedded sub-document for lifecycle configuration."""

    initial_state: str
    states: list[str]
    allowed_transitions: dict[str, list[str]]
    ai_generated: bool
    user_modified: bool


class KnowledgeSchemaDocument(TypedDict):
    """Raw BSON document stored in the ``knowledge_schemas`` collection."""

    _id: str                  # UUID v4 as string
    organization_id: str
    name: str
    description: str | None
    fields: list[SchemaFieldDocument]
    lifecycle: LifecycleDefinitionDocument | None
    version: int
    created_at: datetime
    updated_at: datetime
