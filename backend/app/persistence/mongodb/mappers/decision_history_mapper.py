"""DecisionHistory mapper — Domain ↔ Mongo document."""

from __future__ import annotations

from uuid import UUID

from app.models.decision_history import DecisionHistory
from app.models.enums import DecisionOutcome
from app.persistence.mongodb.documents.decision_history_document import (
    DecisionHistoryDocument,
)


def to_document(decision: DecisionHistory) -> DecisionHistoryDocument:
    """Convert a ``DecisionHistory`` domain model to a Mongo document."""
    return DecisionHistoryDocument(
        _id=str(decision.id),
        organization_id=str(decision.organization_id),
        workspace_id=str(decision.workspace_id),
        recommendation_id=str(decision.recommendation_id),
        asset_id=str(decision.asset_id),
        decided_by=str(decision.decided_by),
        outcome=decision.outcome.value,
        lifecycle_stage=decision.lifecycle_stage,
        notes=decision.notes,
        ai_score_at_decision=decision.ai_score_at_decision,
        ai_rank_at_decision=decision.ai_rank_at_decision,
        created_at=decision.created_at,
        updated_at=decision.updated_at,
    )


def to_domain(doc: DecisionHistoryDocument) -> DecisionHistory:
    """Convert a raw Mongo document to a ``DecisionHistory`` domain model."""
    return DecisionHistory(
        id=UUID(doc["_id"]),
        organization_id=UUID(doc["organization_id"]),
        workspace_id=UUID(doc["workspace_id"]),
        recommendation_id=UUID(doc["recommendation_id"]),
        asset_id=UUID(doc["asset_id"]),
        decided_by=UUID(doc["decided_by"]),
        outcome=DecisionOutcome(doc["outcome"]),
        lifecycle_stage=doc["lifecycle_stage"],
        notes=doc["notes"],
        ai_score_at_decision=doc["ai_score_at_decision"],
        ai_rank_at_decision=doc["ai_rank_at_decision"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )
