"""DecisionHistory domain model.

Decision History is an append-only, permanent audit trail of every
human decision made within a workspace. Records are never mutated or
deleted (architectural invariant from DO_NOT_CHANGE.md).

The Learner agent reads this collection to extract preference signals
and update the workspace's PreferenceProfile.
"""

from uuid import UUID

from pydantic import Field

from app.models.base import AuditedModel
from app.models.enums import DecisionOutcome


class DecisionHistory(AuditedModel):
    """A single immutable record of a human decision.

    Created whenever a human approves, rejects, or overrides a
    recommendation. Once written, this record must never be modified
    (append-only invariant from DO_NOT_CHANGE.md). The ``updated_at``
    field from ``AuditedModel`` is inherited but should remain equal to
    ``created_at`` for decision history records.

    Attributes:
        organization_id: Owning organization — tenant isolation.
        workspace_id: Workspace in which the decision was made.
        recommendation_id: ID of the Recommendation that contained
            the candidate this decision applies to.
        asset_id: ID of the KnowledgeAsset (candidate/option) the
            decision was made about.
        decided_by: User ID of the human who made the decision.
        outcome: The decision outcome.
        lifecycle_stage: The lifecycle stage the asset moved to as a
            result of this decision (matches a stage from the workspace's
            KnowledgeSchema's embedded lifecycle definition).
        notes: Optional free-text rationale provided by the decision
            maker. Valuable input for the Learner.
        ai_score_at_decision: The AI score the candidate had at the
            time of the decision. Stored for learning context — if the
            human overrides a low-scoring candidate, this delta
            carries signal.
        ai_rank_at_decision: The AI rank the candidate held at the
            time of the decision. Same learning-context rationale.
    """

    organization_id: UUID = Field(
        ...,
        description="ID of the owning Organization.",
    )
    workspace_id: UUID = Field(
        ...,
        description="ID of the Workspace where this decision was made.",
    )
    recommendation_id: UUID = Field(
        ...,
        description="ID of the Recommendation containing this candidate.",
    )
    asset_id: UUID = Field(
        ...,
        description="ID of the KnowledgeAsset the decision was made about.",
    )
    decided_by: UUID = Field(
        ...,
        description="User ID of the human who made the decision.",
    )
    outcome: DecisionOutcome = Field(
        ...,
        description="The human decision outcome.",
    )
    lifecycle_stage: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description=(
            "Lifecycle stage the asset moved to as a result of this decision "
            "(matches a state from the workspace's KnowledgeSchema's lifecycle definition)."
        ),
    )
    notes: str | None = Field(
        default=None,
        max_length=5000,
        description="Optional free-text rationale provided by the decision maker.",
    )
    ai_score_at_decision: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="AI score assigned to this candidate at time of decision.",
    )
    ai_rank_at_decision: int | None = Field(
        default=None,
        ge=1,
        description="AI rank of this candidate at time of decision.",
    )
