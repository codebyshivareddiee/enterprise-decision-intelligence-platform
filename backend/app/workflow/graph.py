"""Graph builder for the workflow runtime."""

from typing import Any, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from app.workflow.models import WorkflowState
from app.workflow.context import ExecutionContext
from app.agents.planner.schemas import FailureStrategy


class WorkflowGraphBuilder:
    """Builds a LangGraph StateGraph dynamically from a WorkflowPlan."""
    
    def __init__(self, context: ExecutionContext):
        self.context = context

    def build(self) -> StateGraph:
        """Compile the execution plan into a StateGraph."""
        builder = StateGraph(WorkflowState)
        
        # Add the coordinator node
        builder.add_node("coordinator", self._coordinator_node)
        builder.add_edge(START, "coordinator")

        # Add nodes for each execution step
        for step in self.context.plan.execution_steps:
            node_def = self.context.registry.get(step.agent_name)
            
            # Wrap the registered node to handle validation and state updates
            # Default arguments capture the variables from the loop closure
            def make_node_wrapper(step_to_wrap=step, node_impl=node_def.node_implementation, consumes=node_def.consumes):
                def node_wrapper(state: WorkflowState) -> dict[str, Any]:
                    updates: dict[str, Any] = {}
                    
                    # Validate consumes
                    for artifact in consumes:
                        field_name = artifact.value.lower()
                        if getattr(state, field_name, None) is None:
                            if step_to_wrap.failure_strategy == FailureStrategy.FAIL_PLAN:
                                return {
                                    "failed_steps": [step_to_wrap.step_id],
                                    "errors": [f"Missing artifact {artifact.value} for step {step_to_wrap.step_id}"]
                                }
                    
                    try:
                        # Invoke the actual implementation
                        # Node implementations should return a dict of updates
                        node_updates = node_impl(state)
                        if isinstance(node_updates, dict):
                            updates.update(node_updates)
                        elif isinstance(node_updates, WorkflowState):
                            # If it returns a full state object, extract non-default or changed fields
                            # To be safe, just take the dict representation (excluding unset)
                            updates.update(node_updates.model_dump(exclude_unset=True))
                        
                        # Add completion tracking
                        updates["completed_steps"] = [step_to_wrap.step_id]
                        return updates
                        
                    except Exception as e:
                        error_msg = f"Step {step_to_wrap.step_id} failed: {str(e)}"
                        error_updates = {
                            "failed_steps": [step_to_wrap.step_id],
                            "errors": [error_msg]
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
        def human_review_node(state: WorkflowState) -> dict[str, Any]:
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

    def _coordinator_router(self, state: WorkflowState) -> list[Send] | Literal["human_review", "replan", "__end__"]:
        """Determine which nodes to run next based on the workflow state."""
        if state.requires_replanning:
            return "replan"
            
        # Check if any step that has FAIL_PLAN strategy has failed
        for step in self.context.plan.execution_steps:
            if step.step_id in state.failed_steps and step.failure_strategy == FailureStrategy.FAIL_PLAN:
                return "__end__"
            
        next_steps = []
        all_completed = True
        
        for step in self.context.plan.execution_steps:
            if step.step_id in state.completed_steps or step.step_id in state.failed_steps:
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
