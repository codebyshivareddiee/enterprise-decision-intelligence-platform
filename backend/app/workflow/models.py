"""Data models and state schemas for the workflow runtime."""

import operator
from typing import Annotated, Any

from pydantic import BaseModel, Field

from app.agents.models.explanation import ExplanationResult
from app.agents.models.learner import PreferenceUpdateResult
from app.agents.models.reasoning import ReasoningResult
from app.agents.models.recommendation import RecommendationResult
from app.agents.models.retriever import RetrieverResult
from app.agents.models.validation import ValidationResult


class WorkflowState(BaseModel):
    """Strongly typed state for the LangGraph workflow.

    This state object is passed between nodes in the graph and contains the
    business context as well as the artifacts produced by each step.

    Annotated with operator.add is used for list fields to ensure that when
    parallel nodes return updates, the items are appended rather than overwritten.
    """

    decision_id: str | None = Field(
        default=None, description="The unique execution decision ID"
    )

    # Context
    organization: dict[str, Any] | None = Field(
        default=None, description="Organization context"
    )
    workspace: dict[str, Any] | None = Field(
        default=None, description="Workspace context"
    )
    workspace_context: dict[str, Any] | None = Field(
        default=None, description="Workspace context required by reasoning"
    )
    selected_knowledge_asset_ids: list[str] = Field(
        default_factory=list, description="IDs of knowledge assets to retrieve from"
    )
    selected_business_rule_ids: list[str] = Field(
        default_factory=list, description="IDs of business rules to apply"
    )
    business_rules: list[dict[str, Any]] = Field(
        default_factory=list, description="The fully hydrated business rules"
    )

    # Artifacts (mapped from WorkflowArtifact enum)
    user_request: Any | None = Field(
        default=None, description="The user's original request"
    )
    retrieved_chunks: RetrieverResult | None = Field(
        default=None, description="Knowledge chunks retrieved by the Retriever"
    )
    reasoning_result: ReasoningResult | None = Field(
        default=None, description="Result of applying business rules and AI reasoning"
    )
    recommendation: RecommendationResult | None = Field(
        default=None, description="The ranked and selected recommendation"
    )
    validation_result: ValidationResult | None = Field(
        default=None, description="Validation of the output"
    )
    explanation: ExplanationResult | None = Field(
        default=None, description="Human-readable explanation of the recommendation"
    )
    human_feedback: Any | None = Field(
        default=None, description="Feedback provided by the human reviewer"
    )
    final_decision: Any | None = Field(
        default=None, description="The final confirmed decision"
    )
    preference_update: PreferenceUpdateResult | None = Field(
        default=None, description="Updates to the preference profile"
    )

    # Internal execution tracking
    plan: Any | None = Field(default=None, description="The execution plan")
    current_step_id: str | None = Field(
        default=None, description="ID of current executing step"
    )
    status: str = Field(default="PENDING", description="Workflow status")
    completed_steps: Annotated[list[str], operator.add] = Field(
        default_factory=list,
        description="IDs of steps that have completed successfully",
    )
    failed_steps: Annotated[list[str], operator.add] = Field(
        default_factory=list, description="IDs of steps that failed"
    )
    errors: Annotated[list[str], operator.add] = Field(
        default_factory=list, description="Errors accumulated during execution"
    )
    is_interrupted: bool = Field(
        default=False,
        description="Flag indicating if the workflow is paused for human review",
    )
    requires_replanning: bool = Field(
        default=False, description="Flag indicating if the workflow needs replanning"
    )
    replanning_reason: str | None = Field(
        default=None, description="Reason for replanning if applicable"
    )
