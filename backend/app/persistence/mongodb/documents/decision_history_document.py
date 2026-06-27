"""DecisionHistory MongoDB document schema.

Decision History is append-only — documents are never mutated after insert.
"""

from __future__ import annotations

from datetime import datetime

from typing_extensions import TypedDict


class DecisionHistoryDocument(TypedDict):
    """Raw BSON document stored in the ``decision_history`` collection."""

    _id: str                         # UUID v4 as string
    organization_id: str
    workspace_id: str
    recommendation_id: str           # UUID as string
    asset_id: str                    # UUID as string
    decided_by: str                  # User UUID as string
    outcome: str                     # DecisionOutcome enum value
    lifecycle_stage: str
    notes: str | None
    ai_score_at_decision: float | None
    ai_rank_at_decision: int | None
    created_at: datetime
    updated_at: datetime             # Equals created_at for append-only records
