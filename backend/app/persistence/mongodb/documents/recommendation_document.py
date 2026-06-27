"""Recommendation MongoDB document schema."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from typing_extensions import TypedDict


class RuleEvaluationResultDocument(TypedDict):
    """Embedded sub-document for a single rule evaluation result."""

    rule_id: str      # UUID as string
    rule_name: str
    passed: bool
    is_hard_filter: bool
    reason: str | None


class CandidateScoreDocument(TypedDict):
    """Embedded sub-document for a single candidate score entry."""

    asset_id: str     # UUID as string
    asset_name: str
    ai_score: float | None
    final_rank: int | None
    rule_results: list[RuleEvaluationResultDocument]
    reasoning_notes: str | None
    excluded: bool
    exclusion_reason: str | None


class RecommendationDocument(TypedDict):
    """Raw BSON document stored in the ``recommendations`` collection."""

    _id: str                         # UUID v4 as string
    organization_id: str
    workspace_id: str
    goal: str
    status: str                      # RecommendationStatus enum value
    candidates: list[CandidateScoreDocument]
    top_n: int
    explanation: str | None
    triggered_by: str                # User UUID as string
    plan_snapshot: list[dict[str, Any]]
    error_message: str | None
    created_at: datetime
    updated_at: datetime
