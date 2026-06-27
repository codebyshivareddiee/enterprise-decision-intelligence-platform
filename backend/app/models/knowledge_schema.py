"""KnowledgeSchema domain model.

A KnowledgeSchema defines the field structure expected from knowledge
assets within a workspace. It is configuration, not code — no domain
logic lives here.

Example: a hiring workspace might define fields like
``candidate_name`` (string), ``years_experience`` (integer),
``skills`` (list).
"""

from uuid import UUID

from pydantic import BaseModel, Field

from app.models.base import AuditedModel
from app.models.enums import FieldType


class SchemaField(BaseModel):
    """Definition of a single field within a KnowledgeSchema.

    Attributes:
        name: Machine-readable field name (snake_case recommended).
        label: Human-readable display label for the field.
        field_type: The data type expected for this field's values.
        required: Whether assets must provide a value for this field.
        description: Optional guidance on what this field represents.
        allowed_values: If provided, restricts the field to a fixed set
            of string values (enum-like constraint for string fields).
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Machine-readable field identifier (snake_case).",
    )
    label: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable display label.",
    )
    field_type: FieldType = Field(
        ...,
        description="Data type expected for values of this field.",
    )
    required: bool = Field(
        default=False,
        description="Whether knowledge assets must supply this field.",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional explanation of what this field captures.",
    )
    allowed_values: list[str] | None = Field(
        default=None,
        description=(
            "If set, restricts string fields to this fixed set of values. "
            "Ignored for non-string field types."
        ),
    )


class KnowledgeSchema(AuditedModel):
    """Structural definition for knowledge assets within a workspace.

    A schema is immutable once assets conforming to it have been
    uploaded — changing field definitions after upload would invalidate
    existing data. Version management is a future concern.

    Attributes:
        organization_id: Owning organization — enforces tenant isolation.
        name: Human-readable schema name (e.g. ``"Candidate Profile"``).
        description: Optional description of the schema's purpose and
            the domain it covers.
        fields: Ordered list of field definitions. Field ``name`` values
            must be unique within a schema.
        version: Integer schema version. Start at 1; increment on any
            structural change.
    """

    organization_id: UUID = Field(
        ...,
        description="ID of the owning Organization.",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable schema name.",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional description of the schema's domain purpose.",
    )
    fields: list[SchemaField] = Field(
        default_factory=list,
        description="Ordered field definitions. Field names must be unique.",
    )
    version: int = Field(
        default=1,
        ge=1,
        description="Schema version number. Starts at 1.",
    )
