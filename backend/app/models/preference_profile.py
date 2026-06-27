"""PreferenceProfile domain model.

Preference Profiles represent learned preferences derived from decision
history within a workspace. They are workspace-scoped and never
manually edited — the Learner agent is the only writer
(see DO_NOT_CHANGE.md).

Preference Profiles influence candidate ranking in future
recommendation runs but do not modify business rules.
"""

from uuid import UUID

from pydantic import BaseModel, Field

from app.models.base import AuditedModel
from app.models.enums import LearningScope


class PreferenceSignal(BaseModel):
    """A single learned preference signal extracted from decision history.

    Attributes:
        scope: The level at which this preference applies.
        field_name: The schema field this signal relates to. Required
            when ``scope`` is ``FIELD`` or ``RULE``.
        rule_id: The business rule this signal relates to. Required
            when ``scope`` is ``RULE``.
        description: Human-readable description of the learned
            preference (e.g. ``"Prefers candidates with 7+ years
            experience"``).
        weight: Strength of this preference signal [0.0, 1.0]. Higher
            values give this signal more influence during ranking.
        sample_count: Number of decisions this signal was derived from.
            Higher counts indicate higher confidence.
        confidence: Statistical confidence level [0.0, 1.0] in this
            signal. Derived by the Learner; influences how strongly the
            signal is applied.
    """

    scope: LearningScope = Field(
        ...,
        description="Level at which this preference applies.",
    )
    field_name: str | None = Field(
        default=None,
        max_length=100,
        description="Schema field this preference targets. Set when scope is FIELD.",
    )
    rule_id: UUID | None = Field(
        default=None,
        description="Business rule this preference targets. Set when scope is RULE.",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Human-readable description of the learned preference.",
    )
    weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Preference strength [0.0–1.0].",
    )
    sample_count: int = Field(
        default=0,
        ge=0,
        description="Number of decisions this signal was derived from.",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Statistical confidence in this signal [0.0–1.0].",
    )


class PreferenceProfile(AuditedModel):
    """Workspace-level learned preferences derived from decision history.

    There is at most one PreferenceProfile per workspace. The Learner
    agent is the only writer. Preferences are never manually edited and
    never cross workspace boundaries (DO_NOT_CHANGE.md).

    Attributes:
        organization_id: Owning organization — tenant isolation.
        workspace_id: The workspace these preferences apply to. Unique
            — one profile per workspace.
        signals: List of individual learned preference signals. The
            Learner appends or updates signals after each decision
            event.
        total_decisions_processed: Running count of how many decision
            history records have been processed to build this profile.
        last_updated_by_learner_at: UTC timestamp of the most recent
            Learner run that modified this profile. ``None`` if the
            Learner has not yet run.
    """

    organization_id: UUID = Field(
        ...,
        description="ID of the owning Organization.",
    )
    workspace_id: UUID = Field(
        ...,
        description="ID of the Workspace these preferences apply to (unique per workspace).",
    )
    signals: list[PreferenceSignal] = Field(
        default_factory=list,
        description="Learned preference signals derived from decision history.",
    )
    total_decisions_processed: int = Field(
        default=0,
        ge=0,
        description="Total number of decision records incorporated into this profile.",
    )
    last_updated_by_learner_at: str | None = Field(
        default=None,
        description=(
            "UTC ISO-8601 timestamp of the most recent Learner run. "
            "None if the Learner has not yet processed decisions."
        ),
    )
