"""API Request Models."""

from uuid import UUID

from pydantic import BaseModel, Field


class WorkflowExecuteRequest(BaseModel):
    """Request payload for executing a decision workflow."""

    workspace_id: UUID = Field(
        ..., description="The workspace ID where the workflow should run."
    )
    user_request: str = Field(..., description="The user's objective or prompt.")


class WorkflowResumeRequest(BaseModel):
    """Request payload for resuming a paused workflow (human-in-the-loop)."""

    approved: bool = Field(..., description="Whether the proposed plan was approved.")
    feedback: str | None = Field(
        None, description="Optional feedback if rejected or modified."
    )


class DecisionOutcomeRequest(BaseModel):
    """Request payload to record a decision outcome for continuous learning."""

    decision_id: UUID = Field(..., description="The ID of the decision workflow.")
    human_decision: str = Field(
        ..., description="The actual decision made by the human."
    )
    feedback: str | None = Field(
        None, description="Additional feedback on why this decision was made."
    )
    final_outcome: str | None = Field(
        None, description="The observed real-world outcome (if known)."
    )


class OrganizationCreateRequest(BaseModel):
    """Request payload for self-service organization onboarding."""
    
    name: str = Field(..., min_length=2, max_length=150, description="Organization name")
    description: str | None = Field(None, max_length=1000, description="Optional description")


class WorkspaceCreateRequest(BaseModel):
    """Request payload for creating a new workspace."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="Human-readable workspace name.",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional description of this workspace's purpose.",
    )
    goal: str | None = Field(
        default=None,
        max_length=5000,
        description="The primary objective of this workspace decision context.",
    )
    success_metrics: str | None = Field(
        default=None,
        max_length=5000,
        description="Metrics by which the outcome of decisions in this workspace is evaluated.",
    )
    decision_points: str | None = Field(
        default=None,
        max_length=5000,
        description="Key points of consideration when evaluating options in this workspace.",
    )


class WorkspaceKnowledgeAttachRequest(BaseModel):
    """Request payload to attach existing knowledge assets to a workspace."""

    asset_ids: list[UUID] = Field(
        ...,
        description="List of Organization Knowledge Asset IDs to attach to the workspace."
    )
