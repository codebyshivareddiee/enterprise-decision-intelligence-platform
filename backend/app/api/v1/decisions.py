"""Decisions and Workflow execution endpoints."""

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from langgraph.checkpoint.memory import MemorySaver

from app.agents.planner.planner import Planner
from app.api.dependencies import (
    get_audit_repository,
    get_decision_history_repository,
    get_planner,
    get_workspace_repository,
)
from app.api.v1.models.requests import (
    DecisionOutcomeRequest,
    WorkflowExecuteRequest,
    WorkflowResumeRequest,
)
from app.api.v1.models.response import StandardResponse
from app.api.v1.models.responses import WorkflowExecuteResponse, WorkflowStatusResponse
from app.auth.dependencies import require_authenticated_user, require_role
from app.auth.models import AuditEvent, Role
from app.core.exceptions import EntityNotFound
from app.models.decision_history import DecisionHistory
from app.models.enums import DecisionOutcome
from app.persistence.mongodb.repositories.decision_history_repository import (
    DecisionHistoryRepository,
)
from app.persistence.mongodb.repositories.workspace_repository import (
    WorkspaceRepository,
)
from app.workflow.context import ExecutionContext, RuntimeConfig
from app.workflow.models import WorkflowState
from app.workflow.registry import AgentRegistry
from app.workflow.runtime import WorkflowRuntime

router = APIRouter(
    prefix="/decisions",
    tags=["Decisions"],
    dependencies=[Depends(require_authenticated_user())],
)

# For demonstration, we keep a global MemorySaver instance.
# In production, this would be backed by Redis or Postgres checkpointer.
_checkpointer = MemorySaver()


@router.post(
    "/execute",
    response_model=StandardResponse[WorkflowExecuteResponse],
    summary="Execute a decision workflow",
    dependencies=[Depends(require_role(Role.WORKSPACE_ADMIN))],
)
async def execute_decision(
    request: WorkflowExecuteRequest,
    req: Request,
    planner: Planner = Depends(get_planner),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
    audit_repo=Depends(get_audit_repository),
) -> StandardResponse[WorkflowExecuteResponse]:
    """Invoke the planner and start the LangGraph workflow runtime."""
    workspace = await workspace_repo.get_by_id(request.workspace_id)
    if not workspace:
        raise EntityNotFound("Workspace", str(request.workspace_id))

    # Generate the execution plan

    # In a real app we'd fetch actual schemas, rules, etc.
    # For now, construct the rich decision context.
    workspace_decision_context = workspace.dict()
    # Assume mock logic or actual repositories would fetch these
    workspace_decision_context["business_rules"] = []
    workspace_decision_context["preference_profile"] = {}
    workspace_decision_context["knowledge_schemas"] = []

    import time

    start_time = time.time()

    plan = await planner.generate_plan(
        user_request=request.user_request,
        workspace_decision_context=workspace_decision_context,
    )

    planner_duration = time.time() - start_time
    import structlog

    logger = structlog.get_logger(__name__)
    logger.info(
        "planner_execution_completed",
        plan_generation_duration_ms=round(planner_duration * 1000, 2),
        total_steps=len(plan.execution_steps),
        requires_human_review=plan.requires_human_review,
    )

    # Initialize runtime
    decision_id = uuid.uuid4()

    registry = AgentRegistry()  # Assuming it auto-discovers or we register manually

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
        initial_state=initial_state, thread_id=str(decision_id)
    )

    exec_resp = WorkflowExecuteResponse(
        decision_id=decision_id,
        execution_plan=plan.dict(),
        execution_status=(
            "COMPLETED" if not final_state.is_interrupted else "INTERRUPTED"
        ),
        requires_human_review=final_state.is_interrupted,
        recommendation=None,  # Extract from final_state artifacts if needed
        explanation=None,
        execution_trace=[{"step": step.name} for step in final_state.completed_steps],
    )

    await audit_repo.log_event(
        AuditEvent(
            request_id=getattr(req.state, "request_id", ""),
            user_id=getattr(req.state, "user_id", None),
            organization_id=str(workspace.organization_id),
            workspace_id=str(workspace.id),
            action="execute_decision",
            result="success",
        )
    )

    return StandardResponse(
        success=True,
        data=exec_resp,
        message="Workflow execution started.",
        request_id=getattr(req.state, "request_id", ""),
    )


@router.post(
    "/{decision_id}/resume",
    response_model=StandardResponse[WorkflowStatusResponse],
    summary="Resume a paused workflow",
    dependencies=[Depends(require_role(Role.DECISION_REVIEWER))],
)
async def resume_decision(
    decision_id: UUID,
    request: WorkflowResumeRequest,
    req: Request,
    planner: Planner = Depends(get_planner),
    audit_repo=Depends(get_audit_repository),
) -> StandardResponse[WorkflowStatusResponse]:
    """Resumes a workflow that was paused for human review."""

    # Reconstruct context (in reality, we'd hydrate from DB/checkpoint)
    registry = AgentRegistry()
    context = ExecutionContext(
        plan=None,  # type: ignore
        state=WorkflowState(),
        registry=registry,
        planner=planner,
        config=RuntimeConfig(),
        checkpointer=_checkpointer,
    )

    runtime = WorkflowRuntime(context)

    final_state = await runtime.resume(
        thread_id=str(decision_id), feedback=request.feedback
    )

    status_resp = WorkflowStatusResponse(
        decision_id=decision_id,
        status="COMPLETED" if not final_state.is_interrupted else "INTERRUPTED",
        current_state=final_state.dict(exclude={"plan", "artifacts"}),
        completed_nodes=[s.name for s in final_state.completed_steps],
        failed_nodes=[],
        current_node=None,
        execution_trace=[],
    )

    await audit_repo.log_event(
        AuditEvent(
            request_id=getattr(req.state, "request_id", ""),
            user_id=getattr(req.state, "user_id", None),
            action="resume_decision",
            result="success",
        )
    )

    return StandardResponse(
        success=True,
        data=status_resp,
        message="Workflow resumed successfully.",
        request_id=getattr(req.state, "request_id", ""),
    )


@router.post(
    "/outcome",
    response_model=StandardResponse[DecisionHistory],
    summary="Record a decision outcome",
    dependencies=[Depends(require_role(Role.DECISION_REVIEWER))],
)
async def record_outcome(
    request: DecisionOutcomeRequest,
    req: Request,
    repo: DecisionHistoryRepository = Depends(get_decision_history_repository),
    audit_repo=Depends(get_audit_repository),
) -> StandardResponse[DecisionHistory]:
    """Record a final human decision for a given execution."""

    decision = DecisionHistory(
        organization_id=uuid.uuid4(),  # Mocked org_id
        workspace_id=uuid.uuid4(),  # Mocked workspace_id
        recommendation_id=request.decision_id,
        asset_id=uuid.uuid4(),  # Mocked asset
        decided_by=uuid.uuid4(),  # Mocked user
        outcome=(
            DecisionOutcome.APPROVED
            if "approve" in request.human_decision.lower()
            else DecisionOutcome.REJECTED
        ),
        lifecycle_stage="decided",
        notes=request.feedback,
    )

    created = await repo.create(decision)

    await audit_repo.log_event(
        AuditEvent(
            request_id=getattr(req.state, "request_id", ""),
            user_id=getattr(req.state, "user_id", None),
            action="record_decision_outcome",
            result="success",
        )
    )

    return StandardResponse(
        success=True,
        data=created,
        message="Decision outcome recorded successfully.",
        request_id=getattr(req.state, "request_id", ""),
    )
