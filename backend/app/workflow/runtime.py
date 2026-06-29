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

    async def start(
        self, initial_state: WorkflowState, thread_id: str
    ) -> WorkflowState:
        """Start the execution of the workflow plan."""
        config = {"configurable": {"thread_id": thread_id}}
        import time

        start_time = time.time()

        import structlog

        from app.core.metrics import WORKFLOW_DURATION, WORKFLOWS_TOTAL

        logger = structlog.get_logger(__name__)

        try:
            final_state = await self.graph.ainvoke(initial_state, config=config)

            duration = time.time() - start_time
            WORKFLOWS_TOTAL.labels(status="success").inc()
            WORKFLOW_DURATION.labels(status="success").observe(duration)

            logger.info(
                "workflow_execution_completed",
                workflow_id=thread_id,
                total_duration_ms=round(duration * 1000, 2),
                human_review_required=(
                    final_state.get("is_interrupted", False)
                    if isinstance(final_state, dict)
                    else final_state.is_interrupted
                ),
                success=True,
            )

            if isinstance(final_state, dict):
                return WorkflowState(**final_state)
            return final_state
        except Exception as e:
            duration = time.time() - start_time
            WORKFLOWS_TOTAL.labels(status="error").inc()
            WORKFLOW_DURATION.labels(status="error").observe(duration)

            logger.error(
                "workflow_execution_failed",
                workflow_id=thread_id,
                total_duration_ms=round(duration * 1000, 2),
                success=False,
                error=str(e),
            )
            raise WorkflowExecutionError(f"Workflow execution failed: {str(e)}") from e

    async def resume(self, thread_id: str, feedback: Any = None) -> WorkflowState:
        """Resume an interrupted workflow after human review."""
        config = {"configurable": {"thread_id": thread_id}}

        state_snapshot = await self.graph.aget_state(config)
        if not state_snapshot:
            raise WorkflowExecutionError(
                f"No active state found for thread_id: {thread_id}"
            )

        current_state = state_snapshot.values
        if isinstance(current_state, dict):
            current_state = WorkflowState(**current_state)

        if not current_state.is_interrupted:
            raise WorkflowExecutionError("Workflow is not currently interrupted.")

        update_payload: dict[str, Any] = {"is_interrupted": False}
        if feedback is not None:
            update_payload["human_feedback"] = feedback

        await self.graph.aupdate_state(config, update_payload)

        try:
            final_state = await self.graph.ainvoke(None, config=config)

            if isinstance(final_state, dict):
                return WorkflowState(**final_state)
            return final_state
        except Exception as e:
            raise WorkflowExecutionError(f"Failed to resume workflow: {str(e)}") from e
