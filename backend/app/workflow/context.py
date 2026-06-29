"""Execution context for the workflow runtime."""

from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

from app.agents.planner.planner import Planner
from app.agents.planner.schemas import ExecutionPlan
from app.workflow.models import WorkflowState
from app.workflow.registry import AgentRegistry


class RuntimeConfig(BaseModel):
    """Configuration for the workflow runtime."""

    max_retries: int = Field(
        default=3, description="Maximum number of retries for a step"
    )
    recursion_limit: int = Field(default=50, description="LangGraph recursion limit")


class ExecutionContext(BaseModel):
    """Context object encapsulating everything needed for workflow execution.

    This avoids passing multiple parameters across the runtime layer.
    """

    plan: ExecutionPlan | None = Field(default=None, description="The execution plan from the planner")
    state: WorkflowState = Field(description="The initial or current workflow state")
    registry: AgentRegistry = Field(
        description="The agent registry containing node implementations"
    )
    planner: Planner = Field(description="The planner agent for replanning operations")
    config: RuntimeConfig = Field(
        default_factory=RuntimeConfig, description="Runtime configuration"
    )
    checkpointer: MemorySaver = Field(
        default_factory=MemorySaver,
        description="LangGraph checkpointer for state persistence and human-in-the-loop",
    )

    class Config:
        arbitrary_types_allowed = True
