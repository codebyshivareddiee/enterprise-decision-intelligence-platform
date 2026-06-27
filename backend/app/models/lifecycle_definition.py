"""LifecycleDefinition domain model.

A LifecycleDefinition describes the ordered stages that a decision
moves through within a workspace (e.g., Under Review → Shortlisted →
Decided). It is fully configurable — no stage names are hardcoded.
"""

from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.base import AuditedModel


class LifecycleStage(BaseModel):
    """A single stage within a lifecycle definition.

    Attributes:
        name: Unique, human-readable stage name within this lifecycle
            (e.g. ``"Under Review"``).
        description: Optional guidance on what this stage represents
            and when items enter it.
        order: Zero-based position of this stage in the lifecycle
            sequence. Must be unique within a lifecycle.
        is_terminal: Whether reaching this stage ends the lifecycle for
            an item. At least one stage should be terminal.
        allowed_transitions: Names of stages that items may move to
            from this stage. Empty list means any forward transition
            is permitted; use explicit values to enforce a strict DAG.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique stage name within this lifecycle.",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional explanation of what this stage represents.",
    )
    order: int = Field(
        ...,
        ge=0,
        description="Zero-based position in the lifecycle sequence.",
    )
    is_terminal: bool = Field(
        default=False,
        description="True if reaching this stage ends the lifecycle for an item.",
    )
    allowed_transitions: list[str] = Field(
        default_factory=list,
        description=(
            "Stage names this stage may transition to. Empty = any forward stage "
            "is valid."
        ),
    )


class LifecycleDefinition(AuditedModel):
    """Configuration of the decision lifecycle for a workspace.

    Describes the ordered stages a candidate / option moves through
    during a recommendation workflow. Multiple workspaces may reuse the
    same lifecycle definition or each define their own.

    Attributes:
        organization_id: Owning organization — tenant isolation.
        name: Human-readable lifecycle name (e.g. ``"Standard Hiring
            Pipeline"``).
        description: Optional description of the lifecycle's purpose.
        stages: Ordered list of stage definitions. Stage ``name`` values
            must be unique within the lifecycle. ``order`` values must
            be unique and form a contiguous sequence starting at 0.
    """

    organization_id: UUID = Field(
        ...,
        description="ID of the owning Organization.",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable lifecycle name.",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional description of this lifecycle's purpose.",
    )
    stages: list[LifecycleStage] = Field(
        default_factory=list,
        description="Ordered stage definitions. Stage names must be unique.",
    )

    @field_validator("stages")
    @classmethod
    def stage_names_must_be_unique(cls, stages: list[LifecycleStage]) -> list[LifecycleStage]:
        """Ensure no two stages share the same name within this lifecycle."""
        names = [s.name for s in stages]
        if len(names) != len(set(names)):
            raise ValueError("All stage names within a LifecycleDefinition must be unique.")
        return stages
