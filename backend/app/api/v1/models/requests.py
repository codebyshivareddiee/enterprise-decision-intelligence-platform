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
