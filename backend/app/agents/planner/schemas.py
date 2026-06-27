"""Domain schemas for the Planner Agent."""

from enum import Enum

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Available agents in the platform registry."""

    RETRIEVER = "RETRIEVER"
    REASONING = "REASONING"
    RULE_CHECKER = "RULE_CHECKER"
    RECOMMENDATION = "RECOMMENDATION"
    EXPLANATION = "EXPLANATION"
    LEARNER = "LEARNER"


class FailureStrategy(str, Enum):
    """Strategy to handle a failure of an execution step."""

    FAIL_PLAN = "FAIL_PLAN"
    CONTINUE = "CONTINUE"
    RETRY = "RETRY"
    REPLAN = "REPLAN"


class WorkflowArtifact(str, Enum):
    """Artifacts produced and consumed by workflow steps."""

    USER_REQUEST = "USER_REQUEST"
    RETRIEVED_CHUNKS = "RETRIEVED_CHUNKS"
    REASONING_RESULT = "REASONING_RESULT"
    RECOMMENDATION = "RECOMMENDATION"
    VALIDATION_RESULT = "VALIDATION_RESULT"
    EXPLANATION = "EXPLANATION"
    HUMAN_FEEDBACK = "HUMAN_FEEDBACK"
    FINAL_DECISION = "FINAL_DECISION"
    PREFERENCE_UPDATE = "PREFERENCE_UPDATE"


class ExecutionStep(BaseModel):
    """A single node in the DAG-based execution plan."""

    step_id: str = Field(
        ...,
        description="Unique identifier for this step within the plan (e.g., 'retrieve_knowledge_1').",
    )
    agent_name: AgentType = Field(
        ..., description="The type of agent responsible for executing this step."
    )
    objective: str = Field(..., description="The primary objective of this step.")
    description: str = Field(
        ..., description="Detailed description of what the agent must do."
    )
    consumes: list[WorkflowArtifact] = Field(
        ...,
        description="List of WorkflowArtifacts required before this step can execute.",
    )
    produces: list[WorkflowArtifact] = Field(
        ...,
        description="List of WorkflowArtifacts this step will produce in the workflow state.",
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description="List of step_ids that must complete successfully before this step starts.",
    )
    optional: bool = Field(
        default=False,
        description="If True, failure of this step does not halt the overall plan.",
    )
    failure_strategy: FailureStrategy = Field(
        default=FailureStrategy.FAIL_PLAN, description="What to do if this step fails."
    )
    success_criteria: str = Field(
        ...,
        description="The criteria that must be met for this step to be considered successful.",
    )


class ExecutionPlan(BaseModel):
    """A directed acyclic graph (DAG) representing the workflow execution plan."""

    goal: str = Field(
        ..., description="The overarching goal this plan intends to achieve."
    )
    summary: str = Field(..., description="A concise summary of the plan.")
    reasoning: str = Field(
        ...,
        description="The planner's reasoning for choosing this specific DAG configuration.",
    )
    execution_steps: list[ExecutionStep] = Field(
        ...,
        description="The nodes of the execution DAG. Execution order is determined by depends_on.",
    )
    expected_outputs: list[str] = Field(
        ...,
        description="The final outputs expected from the successful completion of the plan.",
    )
    requires_human_review: bool = Field(
        ...,
        description="True if the plan's outcome or recommendations require human review.",
    )
    human_review_reason: str | None = Field(
        default=None,
        description="Explanation for why human review is required, if applicable.",
    )
    replanning_conditions: list[str] = Field(
        ...,
        description="Conditions under which the Orchestrator should abort the plan and request a new one.",
    )
    completion_conditions: list[str] = Field(
        ...,
        description="Conditions that indicate the plan has successfully met its goal.",
    )
