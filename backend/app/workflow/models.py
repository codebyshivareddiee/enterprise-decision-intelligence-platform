"""Data models and state schemas for the workflow runtime."""

import operator
from typing import Any, Annotated
from pydantic import BaseModel, Field


class WorkflowState(BaseModel):
    """Strongly typed state for the LangGraph workflow.
    
    This state object is passed between nodes in the graph and contains the
    business context as well as the artifacts produced by each step.
    
    Annotated with operator.add is used for list fields to ensure that when
    parallel nodes return updates, the items are appended rather than overwritten.
    """
    # Context
    organization: dict[str, Any] | None = Field(default=None, description="Organization context")
    workspace: dict[str, Any] | None = Field(default=None, description="Workspace context")
    
    # Artifacts (mapped from WorkflowArtifact enum)
    user_request: Any | None = Field(default=None, description="The user's original request")
    retrieved_chunks: Any | None = Field(default=None, description="Knowledge chunks retrieved by the Retriever")
    reasoning_result: Any | None = Field(default=None, description="Result of applying business rules and AI reasoning")
    recommendation: Any | None = Field(default=None, description="The ranked and selected recommendation")
    validation_result: Any | None = Field(default=None, description="Validation of the output")
    explanation: Any | None = Field(default=None, description="Human-readable explanation of the recommendation")
    human_feedback: Any | None = Field(default=None, description="Feedback provided by the human reviewer")
    final_decision: Any | None = Field(default=None, description="The final confirmed decision")
    preference_update: Any | None = Field(default=None, description="Updates to the preference profile")
    
    # Internal execution tracking
    completed_steps: Annotated[list[str], operator.add] = Field(default_factory=list, description="IDs of steps that have completed successfully")
    failed_steps: Annotated[list[str], operator.add] = Field(default_factory=list, description="IDs of steps that failed")
    errors: Annotated[list[str], operator.add] = Field(default_factory=list, description="Errors accumulated during execution")
    is_interrupted: bool = Field(default=False, description="Flag indicating if the workflow is paused for human review")
    requires_replanning: bool = Field(default=False, description="Flag indicating if the workflow needs replanning")
    replanning_reason: str | None = Field(default=None, description="Reason for replanning if applicable")
