"""Decisions and Workflow execution endpoints."""

from typing import Any
from uuid import UUID
import uuid

from fastapi import APIRouter, Depends

from langgraph.checkpoint.memory import MemorySaver

from app.agents.planner.planner import Planner
from app.api.dependencies import (
    get_ai_manager,
    get_decision_history_repository,
    get_planner,
    get_workspace_repository,
)
from app.api.v1.models.requests import (
    DecisionOutcomeRequest,
    WorkflowExecuteRequest,
    WorkflowResumeRequest,
)
from app.api.v1.models.responses import WorkflowExecuteResponse, WorkflowStatusResponse
from app.core.exceptions import EntityNotFound
from app.models.decision_history import DecisionHistory
from app.models.enums import DecisionOutcome
from app.persistence.mongodb.repositories.decision_history_repository import DecisionHistoryRepository
from app.persistence.mongodb.repositories.workspace_repository import WorkspaceRepository
from app.workflow.context import ExecutionContext, RuntimeConfig
from app.workflow.models import WorkflowState
from app.workflow.registry import AgentRegistry
from app.workflow.runtime import WorkflowRuntime
from app.auth.dependencies import get_current_user, require_permission
from app.auth.permissions import Permission

router = APIRouter(
    prefix="/decisions", 
    tags=["Decisions"],
    dependencies=[Depends(get_current_user)]
)

# For demonstration, we keep a global MemorySaver instance.
# In production, this would be backed by Redis or Postgres checkpointer.
_checkpointer = MemorySaver()


@router.post(
    "/execute",
    response_model=WorkflowExecuteResponse,
    summary="Execute a decision workflow",
    dependencies=[Depends(require_permission(Permission.EXECUTE_WORKFLOWS))],
)
async def execute_decision(
    request: WorkflowExecuteRequest,
    planner: Planner = Depends(get_planner),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
) -> WorkflowExecuteResponse:
    """Invoke the planner and start the LangGraph workflow runtime."""
    workspace = await workspace_repo.get_by_id(request.workspace_id)
    if not workspace:
        raise EntityNotFound("Workspace", str(request.workspace_id))
        
    # Generate the execution plan
    plan = await planner.generate_plan(
        user_request=request.user_request,
        workspace=workspace.dict()
    )
    
    # Initialize runtime
    decision_id = uuid.uuid4()
    
    registry = AgentRegistry() # Assuming it auto-discovers or we register manually
    
    initial_state = WorkflowState(
        messages=[],
        plan=plan,
        current_step=0,
        completed_steps=[],
        artifacts={},
        business_context={},
    )
    
    context = ExecutionContext(
        plan=plan,
        state=initial_state,
        registry=registry,
        planner=planner,
        config=RuntimeConfig(),
        checkpointer=_checkpointer,
    )
    
    runtime = WorkflowRuntime(context)
    
    # Execute workflow
    final_state = await runtime.start(
        initial_state=initial_state, 
        thread_id=str(decision_id)
    )
    
    return WorkflowExecuteResponse(
        decision_id=decision_id,
        execution_plan=plan.dict(),
        execution_status="COMPLETED" if not final_state.is_interrupted else "INTERRUPTED",
        requires_human_review=final_state.is_interrupted,
        recommendation=None, # Extract from final_state artifacts if needed
        explanation=None,
        execution_trace=[{"step": step.name} for step in final_state.completed_steps],
    )


@router.post(
    "/{decision_id}/resume",
    response_model=WorkflowStatusResponse,
    summary="Resume a paused workflow",
    dependencies=[Depends(require_permission(Permission.RESUME_WORKFLOWS))],
)
async def resume_decision(
    decision_id: UUID,
    request: WorkflowResumeRequest,
    planner: Planner = Depends(get_planner),
) -> WorkflowStatusResponse:
    """Resumes a workflow that was paused for human review."""
    
    # Reconstruct context (in reality, we'd hydrate from DB/checkpoint)
    registry = AgentRegistry()
    context = ExecutionContext(
        plan=None, # type: ignore (In a real app, hydrate this)
        state=WorkflowState(), 
        registry=registry,
        planner=planner,
        config=RuntimeConfig(),
        checkpointer=_checkpointer,
    )
    
    runtime = WorkflowRuntime(context)
    
    final_state = await runtime.resume(
        thread_id=str(decision_id), 
        feedback=request.feedback
    )
    
    return WorkflowStatusResponse(
        decision_id=decision_id,
        status="COMPLETED" if not final_state.is_interrupted else "INTERRUPTED",
        current_state=final_state.dict(exclude={"plan", "artifacts"}),
        completed_nodes=[s.name for s in final_state.completed_steps],
        failed_nodes=[],
        current_node=None,
        execution_trace=[],
    )


@router.post(
    "/outcome",
    response_model=DecisionHistory,
    summary="Record a decision outcome",
    dependencies=[Depends(require_permission(Permission.RECORD_OUTCOMES))],
)
async def record_outcome(
    request: DecisionOutcomeRequest,
    repo: DecisionHistoryRepository = Depends(get_decision_history_repository),
) -> DecisionHistory:
    """Record a final human decision for a given execution."""
    
    decision = DecisionHistory(
        organization_id=uuid.uuid4(), # Mocked org_id
        workspace_id=uuid.uuid4(),    # Mocked workspace_id
        recommendation_id=request.decision_id,
        asset_id=uuid.uuid4(),        # Mocked asset
        decided_by=uuid.uuid4(),      # Mocked user
        outcome=DecisionOutcome.APPROVED if "approve" in request.human_decision.lower() else DecisionOutcome.REJECTED,
        lifecycle_stage="decided",
        notes=request.feedback,
    )
    
    return await repo.create(decision)
