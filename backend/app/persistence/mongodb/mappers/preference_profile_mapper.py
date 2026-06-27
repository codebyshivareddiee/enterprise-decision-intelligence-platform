"""PreferenceProfile mapper — Domain ↔ Mongo document."""

from __future__ import annotations

from uuid import UUID

from app.models.enums import LearningScope
from app.models.preference_profile import PreferenceProfile, PreferenceSignal
from app.persistence.mongodb.documents.preference_profile_document import (
    PreferenceProfileDocument,
    PreferenceSignalDocument,
)

# ---------------------------------------------------------------------------
# PreferenceSignal helpers
# ---------------------------------------------------------------------------


def _signal_to_document(signal: PreferenceSignal) -> PreferenceSignalDocument:
    return PreferenceSignalDocument(
        scope=signal.scope.value,
        field_name=signal.field_name,
        rule_id=str(signal.rule_id) if signal.rule_id is not None else None,
        description=signal.description,
        weight=signal.weight,
        sample_count=signal.sample_count,
        confidence=signal.confidence,
    )


def _signal_to_domain(doc: PreferenceSignalDocument) -> PreferenceSignal:
    return PreferenceSignal(
        scope=LearningScope(doc["scope"]),
        field_name=doc["field_name"],
        rule_id=UUID(doc["rule_id"]) if doc["rule_id"] is not None else None,
        description=doc["description"],
        weight=doc["weight"],
        sample_count=doc["sample_count"],
        confidence=doc["confidence"],
    )


# ---------------------------------------------------------------------------
# PreferenceProfile mapper
# ---------------------------------------------------------------------------


def to_document(profile: PreferenceProfile) -> PreferenceProfileDocument:
    """Convert a ``PreferenceProfile`` domain model to a Mongo document."""
    return PreferenceProfileDocument(
        _id=str(profile.id),
        organization_id=str(profile.organization_id),
        workspace_id=str(profile.workspace_id),
        signals=[_signal_to_document(s) for s in profile.signals],
        total_decisions_processed=profile.total_decisions_processed,
        last_updated_by_learner_at=profile.last_updated_by_learner_at,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def to_domain(doc: PreferenceProfileDocument) -> PreferenceProfile:
    """Convert a raw Mongo document to a ``PreferenceProfile`` domain model."""
    return PreferenceProfile(
        id=UUID(doc["_id"]),
        organization_id=UUID(doc["organization_id"]),
        workspace_id=UUID(doc["workspace_id"]),
        signals=[_signal_to_domain(s) for s in doc["signals"]],
        total_decisions_processed=doc["total_decisions_processed"],
        last_updated_by_learner_at=doc["last_updated_by_learner_at"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )
