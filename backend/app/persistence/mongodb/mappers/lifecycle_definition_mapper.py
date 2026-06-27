"""LifecycleDefinition mapper — Domain ↔ Mongo document."""

from __future__ import annotations

from uuid import UUID

from app.models.lifecycle_definition import LifecycleDefinition, LifecycleStage
from app.persistence.mongodb.documents.lifecycle_definition_document import (
    LifecycleDefinitionDocument,
    LifecycleStageDocument,
)


# ---------------------------------------------------------------------------
# LifecycleStage helpers
# ---------------------------------------------------------------------------


def _stage_to_document(stage: LifecycleStage) -> LifecycleStageDocument:
    return LifecycleStageDocument(
        name=stage.name,
        description=stage.description,
        order=stage.order,
        is_terminal=stage.is_terminal,
        allowed_transitions=list(stage.allowed_transitions),
    )


def _stage_to_domain(doc: LifecycleStageDocument) -> LifecycleStage:
    return LifecycleStage(
        name=doc["name"],
        description=doc["description"],
        order=doc["order"],
        is_terminal=doc["is_terminal"],
        allowed_transitions=doc["allowed_transitions"],
    )


# ---------------------------------------------------------------------------
# LifecycleDefinition mapper
# ---------------------------------------------------------------------------


def to_document(lifecycle: LifecycleDefinition) -> LifecycleDefinitionDocument:
    """Convert a ``LifecycleDefinition`` domain model to a Mongo document."""
    return LifecycleDefinitionDocument(
        _id=str(lifecycle.id),
        organization_id=str(lifecycle.organization_id),
        name=lifecycle.name,
        description=lifecycle.description,
        stages=[_stage_to_document(s) for s in lifecycle.stages],
        created_at=lifecycle.created_at,
        updated_at=lifecycle.updated_at,
    )


def to_domain(doc: LifecycleDefinitionDocument) -> LifecycleDefinition:
    """Convert a raw Mongo document to a ``LifecycleDefinition`` domain model."""
    return LifecycleDefinition(
        id=UUID(doc["_id"]),
        organization_id=UUID(doc["organization_id"]),
        name=doc["name"],
        description=doc["description"],
        stages=[_stage_to_domain(s) for s in doc["stages"]],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )
