"""KnowledgeSchema mapper — Domain ↔ Mongo document."""

from __future__ import annotations

from uuid import UUID

from app.models.enums import FieldType
from app.models.knowledge_schema import KnowledgeSchema, SchemaField
from app.persistence.mongodb.documents.knowledge_schema_document import (
    KnowledgeSchemaDocument,
    SchemaFieldDocument,
)


# ---------------------------------------------------------------------------
# SchemaField helpers
# ---------------------------------------------------------------------------


def _field_to_document(field: SchemaField) -> SchemaFieldDocument:
    return SchemaFieldDocument(
        name=field.name,
        label=field.label,
        field_type=field.field_type.value,
        required=field.required,
        description=field.description,
        allowed_values=field.allowed_values,
    )


def _field_to_domain(doc: SchemaFieldDocument) -> SchemaField:
    return SchemaField(
        name=doc["name"],
        label=doc["label"],
        field_type=FieldType(doc["field_type"]),
        required=doc["required"],
        description=doc["description"],
        allowed_values=doc["allowed_values"],
    )


# ---------------------------------------------------------------------------
# KnowledgeSchema mapper
# ---------------------------------------------------------------------------


def to_document(schema: KnowledgeSchema) -> KnowledgeSchemaDocument:
    """Convert a ``KnowledgeSchema`` domain model to a Mongo document."""
    return KnowledgeSchemaDocument(
        _id=str(schema.id),
        organization_id=str(schema.organization_id),
        name=schema.name,
        description=schema.description,
        fields=[_field_to_document(f) for f in schema.fields],
        version=schema.version,
        created_at=schema.created_at,
        updated_at=schema.updated_at,
    )


def to_domain(doc: KnowledgeSchemaDocument) -> KnowledgeSchema:
    """Convert a raw Mongo document to a ``KnowledgeSchema`` domain model."""
    return KnowledgeSchema(
        id=UUID(doc["_id"]),
        organization_id=UUID(doc["organization_id"]),
        name=doc["name"],
        description=doc["description"],
        fields=[_field_to_domain(f) for f in doc["fields"]],
        version=doc["version"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )
