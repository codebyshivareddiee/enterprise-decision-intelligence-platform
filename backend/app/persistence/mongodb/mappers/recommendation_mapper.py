"""Recommendation mapper — Domain ↔ Mongo document."""

from __future__ import annotations

from uuid import UUID

from app.models.enums import RecommendationStatus
from app.models.recommendation import (
    CandidateScore,
    Recommendation,
    RuleEvaluationResult,
)
from app.persistence.mongodb.documents.recommendation_document import (
    CandidateScoreDocument,
    RecommendationDocument,
    RuleEvaluationResultDocument,
)


# ---------------------------------------------------------------------------
# RuleEvaluationResult helpers
# ---------------------------------------------------------------------------


def _rule_result_to_document(result: RuleEvaluationResult) -> RuleEvaluationResultDocument:
    return RuleEvaluationResultDocument(
        rule_id=str(result.rule_id),
        rule_name=result.rule_name,
        passed=result.passed,
        is_hard_filter=result.is_hard_filter,
        reason=result.reason,
    )


def _rule_result_to_domain(doc: RuleEvaluationResultDocument) -> RuleEvaluationResult:
    return RuleEvaluationResult(
        rule_id=UUID(doc["rule_id"]),
        rule_name=doc["rule_name"],
        passed=doc["passed"],
        is_hard_filter=doc["is_hard_filter"],
        reason=doc["reason"],
    )


# ---------------------------------------------------------------------------
# CandidateScore helpers
# ---------------------------------------------------------------------------


def _candidate_to_document(candidate: CandidateScore) -> CandidateScoreDocument:
    return CandidateScoreDocument(
        asset_id=str(candidate.asset_id),
        asset_name=candidate.asset_name,
        ai_score=candidate.ai_score,
        final_rank=candidate.final_rank,
        rule_results=[_rule_result_to_document(r) for r in candidate.rule_results],
        reasoning_notes=candidate.reasoning_notes,
        excluded=candidate.excluded,
        exclusion_reason=candidate.exclusion_reason,
    )


def _candidate_to_domain(doc: CandidateScoreDocument) -> CandidateScore:
    return CandidateScore(
        asset_id=UUID(doc["asset_id"]),
        asset_name=doc["asset_name"],
        ai_score=doc["ai_score"],
        final_rank=doc["final_rank"],
        rule_results=[_rule_result_to_domain(r) for r in doc["rule_results"]],
        reasoning_notes=doc["reasoning_notes"],
        excluded=doc["excluded"],
        exclusion_reason=doc["exclusion_reason"],
    )


# ---------------------------------------------------------------------------
# Recommendation mapper
# ---------------------------------------------------------------------------


def to_document(recommendation: Recommendation) -> RecommendationDocument:
    """Convert a ``Recommendation`` domain model to a Mongo document."""
    return RecommendationDocument(
        _id=str(recommendation.id),
        organization_id=str(recommendation.organization_id),
        workspace_id=str(recommendation.workspace_id),
        goal=recommendation.goal,
        status=recommendation.status.value,
        candidates=[_candidate_to_document(c) for c in recommendation.candidates],
        top_n=recommendation.top_n,
        explanation=recommendation.explanation,
        triggered_by=str(recommendation.triggered_by),
        plan_snapshot=list(recommendation.plan_snapshot),
        error_message=recommendation.error_message,
        created_at=recommendation.created_at,
        updated_at=recommendation.updated_at,
    )


def to_domain(doc: RecommendationDocument) -> Recommendation:
    """Convert a raw Mongo document to a ``Recommendation`` domain model."""
    return Recommendation(
        id=UUID(doc["_id"]),
        organization_id=UUID(doc["organization_id"]),
        workspace_id=UUID(doc["workspace_id"]),
        goal=doc["goal"],
        status=RecommendationStatus(doc["status"]),
        candidates=[_candidate_to_domain(c) for c in doc["candidates"]],
        top_n=doc["top_n"],
        explanation=doc["explanation"],
        triggered_by=UUID(doc["triggered_by"]),
        plan_snapshot=doc["plan_snapshot"],
        error_message=doc["error_message"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )
