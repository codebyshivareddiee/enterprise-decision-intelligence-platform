"""The LangGraph execution runtime (Orchestrator)."""

from typing import Any

from app.workflow.context import ExecutionContext
from app.workflow.exceptions import WorkflowExecutionError
from app.workflow.graph import WorkflowGraphBuilder
from app.workflow.models import WorkflowState


class WorkflowRuntime:
    """The Runtime orchestrator for executing workflow plans.

    It is purely an execution engine. It never makes business decisions or generates plans.
    """

    def __init__(self, context: ExecutionContext):
        self.context = context
        self.builder = WorkflowGraphBuilder(self.context)
        self.graph = self.builder.build()

    def start(self, initial_state: WorkflowState, thread_id: str) -> WorkflowState:
        """Start the execution of the workflow plan."""
        config = {"configurable": {"thread_id": thread_id}}

        try:
            # stream_mode="values" will yield state updates.
            # We just want to invoke it to completion or interrupt.
            final_state = self.graph.invoke(initial_state, config=config)

            # Since LangGraph returns dicts for state when using TypedDict, or Pydantic if configured,
            # we ensure the return is always a WorkflowState object.
            if isinstance(final_state, dict):
                return WorkflowState(**final_state)
            return final_state
        except Exception as e:
            raise WorkflowExecutionError(f"Workflow execution failed: {str(e)}") from e

    def resume(self, thread_id: str, feedback: Any = None) -> WorkflowState:
        """Resume an interrupted workflow after human review."""
        config = {"configurable": {"thread_id": thread_id}}

        # Get the current state
        state_snapshot = self.graph.get_state(config)
        if not state_snapshot:
            raise WorkflowExecutionError(
                f"No active state found for thread_id: {thread_id}"
            )

        current_state = state_snapshot.values
        if isinstance(current_state, dict):
            current_state = WorkflowState(**current_state)

        if not current_state.is_interrupted:
            raise WorkflowExecutionError("Workflow is not currently interrupted.")

        # Clear the interrupt flag and apply feedback
        update_payload: dict[str, Any] = {"is_interrupted": False}
        if feedback is not None:
            update_payload["human_feedback"] = feedback

        # Update state manually and resume
        self.graph.update_state(config, update_payload)

        try:
            final_state = self.graph.invoke(None, config=config)

            if isinstance(final_state, dict):
                return WorkflowState(**final_state)
            return final_state
        except Exception as e:
            raise WorkflowExecutionError(f"Failed to resume workflow: {str(e)}") from e
