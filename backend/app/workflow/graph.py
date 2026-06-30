"""Graph builder for the workflow runtime."""

from typing import Any, Literal

import structlog
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from app.agents.planner.schemas import FailureStrategy, WorkflowArtifact
from app.workflow.context import ExecutionContext
from app.workflow.models import WorkflowState

logger = structlog.get_logger(__name__)


class WorkflowGraphBuilder:
    """Builds a LangGraph StateGraph dynamically from a WorkflowPlan."""

    def __init__(self, context: ExecutionContext):
        self.context = context

    def build(self) -> Any:
        """Compile the execution plan into a StateGraph."""
        if not self.context.plan:
            raise ValueError("Execution plan is missing from context.")

        builder = StateGraph(WorkflowState)

        # Add the coordinator node
        builder.add_node("coordinator", self._coordinator_node)
        builder.add_edge(START, "coordinator")

        # Add nodes for each execution step
        for step in self.context.plan.execution_steps:
            node_def = self.context.registry.get(step.agent_name)
            if not node_def:
                raise ValueError(f"Agent '{step.agent_name}' not found in registry.")

            # Wrap the registered node to handle validation and state updates
            # Default arguments capture the variables from the loop closure
            def make_node_wrapper(
                step_to_wrap=step,
                node_impl=node_def.node_implementation,
                consumes=node_def.consumes,
                produces=node_def.produces,
            ):
                async def node_wrapper(state: WorkflowState) -> dict[str, Any]:
                    import inspect
                    import time
                    from app.workflow.events import event_bus

                    start_time = time.time()
                    workflow_id = state.get("decision_id", "unknown") if isinstance(state, dict) else getattr(state, "decision_id", "unknown")
                    
                    if isinstance(state, dict):
                        state["current_step_id"] = step_to_wrap.step_id
                    else:
                        state.current_step_id = step_to_wrap.step_id
                        
                    logger.info(f"[{step_to_wrap.step_id}] Started execution...")
                    
                    await event_bus.publish(workflow_id, "agent_started", {
                        "step_id": step_to_wrap.step_id,
                        "agent_name": step_to_wrap.agent_name,
                        "status": "running",
                        "progress": 0
                    })

                    consumed_names = [a.value for a in consumes]
                    if consumed_names:
                        # Serialize inputs safely using pydantic if possible
                        input_data = {}
                        for a in consumes:
                            field_key = a.value.lower()
                            val = state.get(field_key) if isinstance(state, dict) else getattr(state, field_key, None)
                            if val and hasattr(val, "model_dump"):
                                input_data[a.value.lower()] = val.model_dump()
                            else:
                                input_data[a.value.lower()] = val
                                
                        logger.info(
                            f"[{step_to_wrap.step_id}] Consuming artifacts: {consumed_names}",
                            inputs=input_data
                        )
                        for name in consumed_names:
                            await event_bus.publish(workflow_id, "artifact_consumed", {
                                "step_id": step_to_wrap.step_id,
                                "agent_name": step_to_wrap.agent_name,
                                "artifact_name": name
                            })

                    updates: dict[str, Any] = {}

                    # Validate consumes
                    for artifact in consumes:
                        field_name = artifact.value.lower()
                        val = state.get(field_name) if isinstance(state, dict) else getattr(state, field_name, None)
                        if val is None:
                            error_msg = f"Missing artifact {artifact.value} for step {step_to_wrap.step_id}"
                            logger.error(f"[{step_to_wrap.step_id}] ERROR: {error_msg}")
                            if (
                                step_to_wrap.failure_strategy
                                == FailureStrategy.FAIL_PLAN
                            ):
                                return {
                                    "failed_steps": [step_to_wrap.step_id],
                                    "errors": [error_msg],
                                 }

                    # Note: We omit updating step status in DB synchronously here to avoid Motor client conflicts
                    # in this fast-running demo workflow.

                    try:
                        # Invoke the actual implementation (async or sync)
                        if inspect.iscoroutinefunction(node_impl):
                            node_updates = await node_impl(state)
                        else:
                            node_updates = node_impl(state)
                            if inspect.isawaitable(node_updates):
                                node_updates = await node_updates

                        if isinstance(node_updates, WorkflowState):
                            dumped = node_updates.model_dump()
                            produced_keys = {a.value.lower() for a in produces}
                            node_updates = {
                                k: dumped[k] for k in produced_keys if k in dumped
                            }

                        if isinstance(node_updates, dict):
                            # Allow whatever the agent explicitly put in the dict, plus our extracted produces
                            updates.update(node_updates)

                        # Validate produces
                        produced_names = [a.value for a in produces]
                        if produced_names:
                            logger.debug(
                                f"[{step_to_wrap.step_id}] Expected to produce: {produced_names}"
                            )

                        for artifact in produces:
                            field_name = artifact.value.lower()
                            state_val = state.get(field_name) if isinstance(state, dict) else getattr(state, field_name, None)
                            if (
                                updates.get(field_name) is None
                                and state_val is None
                            ):
                                raise ValueError(
                                    f"Agent failed to produce declared artifact: {artifact.value}"
                                )

                        # Add completion tracking
                        updates["completed_steps"] = [step_to_wrap.step_id]

                        execution_time = time.time() - start_time

                        from app.core.metrics import (
                            AGENT_ARTIFACTS,
                            AGENT_DURATION,
                            AGENT_EXECUTIONS_TOTAL,
                        )

                        AGENT_EXECUTIONS_TOTAL.labels(
                            agent_type=step_to_wrap.agent_name, status="success"
                        ).inc()
                        AGENT_DURATION.labels(
                            agent_type=step_to_wrap.agent_name
                        ).observe(execution_time)
                        AGENT_ARTIFACTS.labels(
                            agent_type=step_to_wrap.agent_name,
                            artifact_action="consumed",
                        ).inc(len(consumes))
                        AGENT_ARTIFACTS.labels(
                            agent_type=step_to_wrap.agent_name,
                            artifact_action="produced",
                        ).inc(len(produces))

                        logger.info(
                            f"[{step_to_wrap.step_id}] Success in {execution_time:.2f}s",
                            agent_type=step_to_wrap.agent_name,
                            execution_duration_ms=round(execution_time * 1000, 2),
                            success=True,
                            artifacts_consumed=len(consumes),
                            artifacts_produced=len(produces),
                        )

                        available_artifacts = []
                        for art in WorkflowArtifact:
                            art_val = state.get(art.value.lower()) if isinstance(state, dict) else getattr(state, art.value.lower(), None)
                            if art_val is not None or art.value.lower() in updates:
                                available_artifacts.append(art.value)
                        
                        # Serialize outputs safely for logging
                        output_data = {}
                        for k, v in updates.items():
                            if v and hasattr(v, "model_dump"):
                                output_data[k] = v.model_dump()
                            else:
                                output_data[k] = v
                                
                        logger.info(
                            f"[{step_to_wrap.step_id}] Agent output:",
                            updates=output_data,
                            available_artifacts=available_artifacts
                        )
                        
                        for name in produced_names:
                            await event_bus.publish(workflow_id, "artifact_created", {
                                "step_id": step_to_wrap.step_id,
                                "agent_name": step_to_wrap.agent_name,
                                "artifact_name": name
                            })
                            
                        metrics = {}
                        if "retrieved_chunks" in updates:
                            rc = updates["retrieved_chunks"]
                            if hasattr(rc, "chunks"):
                                metrics["retrieved_chunk_count"] = len(rc.chunks)
                        if "reasoning_result" in updates:
                            rr = updates["reasoning_result"]
                            if hasattr(rr, "confidence_score"):
                                metrics["confidence_score"] = rr.confidence_score
                            elif hasattr(rr, "confidence"):
                                metrics["confidence_score"] = rr.confidence
                                
                        await event_bus.publish(workflow_id, "agent_completed", {
                            "step_id": step_to_wrap.step_id,
                            "agent_name": step_to_wrap.agent_name,
                            "duration_ms": round(execution_time * 1000, 2),
                            "status": "completed",
                            "progress": 100,
                            "output_artifacts": produced_names,
                            "metrics": metrics
                        })

                        return updates

                    except Exception as e:
                        execution_time = time.time() - start_time

                        from app.core.metrics import (
                            AGENT_ARTIFACTS,
                            AGENT_DURATION,
                            AGENT_EXECUTIONS_TOTAL,
                        )

                        AGENT_EXECUTIONS_TOTAL.labels(
                            agent_type=step_to_wrap.agent_name, status="error"
                        ).inc()
                        AGENT_DURATION.labels(
                            agent_type=step_to_wrap.agent_name
                        ).observe(execution_time)
                        AGENT_ARTIFACTS.labels(
                            agent_type=step_to_wrap.agent_name,
                            artifact_action="consumed",
                        ).inc(len(consumes))

                        error_msg = f"Step {step_to_wrap.step_id} failed: {str(e)}"
                        logger.error(
                            f"[{step_to_wrap.step_id}] Failed in {execution_time:.2f}s: {error_msg}",
                            agent_type=step_to_wrap.agent_name,
                            execution_duration_ms=round(execution_time * 1000, 2),
                            success=False,
                            failure_reason=str(e),
                            artifacts_consumed=len(consumes),
                            artifacts_produced=0,
                        )
                        
                        await event_bus.publish(workflow_id, "agent_failed", {
                            "step_id": step_to_wrap.step_id,
                            "agent_name": step_to_wrap.agent_name,
                            "duration_ms": round(execution_time * 1000, 2),
                            "status": "failed",
                            "error": error_msg
                        })

                        error_updates: dict[str, Any] = {
                            "failed_steps": [step_to_wrap.step_id],
                            "errors": [error_msg],
                        }
                        if step_to_wrap.failure_strategy == FailureStrategy.REPLAN:
                            error_updates["requires_replanning"] = True
                            error_updates["replanning_reason"] = error_msg
                        return error_updates

                return node_wrapper

            # Add the wrapped node to the graph
            builder.add_node(step.step_id, make_node_wrapper())
            # All steps transition back to the coordinator
            builder.add_edge(step.step_id, "coordinator")

        # Human Review Node
        async def human_review_node(state: WorkflowState) -> dict[str, Any]:
            from app.workflow.events import event_bus
            workflow_id = state.get("decision_id", "unknown") if isinstance(state, dict) else getattr(state, "decision_id", "unknown")
            await event_bus.publish(workflow_id, "workflow_paused", {
                "reason": "human_review"
            })
            return {"is_interrupted": True}

        builder.add_node("human_review", human_review_node)
        builder.add_edge("human_review", END)

        # Replanning Node
        def replan_node(state: WorkflowState) -> dict[str, Any]:
            # This is a placeholder for triggering actual replanning via the Planner.
            # Real implementation would call self.context.planner.generate_plan(...)
            return {"requires_replanning": True}

        builder.add_node("replan", replan_node)
        builder.add_edge("replan", END)

        # The coordinator uses conditional edges to trigger steps
        builder.add_conditional_edges("coordinator", self._coordinator_router)

        # Compile the graph with the checkpointer
        return builder.compile(checkpointer=self.context.checkpointer)

    def _coordinator_node(self, state: WorkflowState) -> dict[str, Any]:
        """A pass-through node whose only purpose is routing."""
        return {}

    def _coordinator_router(
        self, state: WorkflowState
    ) -> list[Send] | Literal["human_review", "replan", "__end__"]:
        """Determine which nodes to run next based on the workflow state."""
        if not self.context.plan:
            return "__end__"

        if state.requires_replanning:
            return "replan"

        # Check if any step that has FAIL_PLAN strategy has failed
        for step in self.context.plan.execution_steps:
            if (
                step.step_id in state.failed_steps
                and step.failure_strategy == FailureStrategy.FAIL_PLAN
            ):
                return "__end__"

        next_steps = []
        all_completed = True

        for step in self.context.plan.execution_steps:
            if (
                step.step_id in state.completed_steps
                or step.step_id in state.failed_steps
            ):
                continue

            all_completed = False

            # Check if dependencies are met
            deps_met = all(dep in state.completed_steps for dep in step.depends_on)
            if deps_met:
                next_steps.append(Send(step.step_id, state))

        if next_steps:
            return next_steps

        if all_completed:
            if self.context.plan.requires_human_review:
                return "human_review"
            return "__end__"

        # If we reach here, we have incomplete steps but no dependencies met.
        # This implies a deadlock or a dependency failed but did not abort the plan (optional=True).
        # We end execution gracefully.
        return "__end__"
