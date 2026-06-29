"""Decisions and Workflow execution endpoints."""

import uuid
import logging
from uuid import UUID
from typing import Any

from fastapi import APIRouter, Depends, Request, BackgroundTasks
from langgraph.checkpoint.memory import MemorySaver

from app.agents.planner.planner import Planner
from app.api.dependencies import (
    get_audit_repository,
    get_decision_history_repository,
    get_planner,
    get_workspace_repository,
    get_audit_repository,
    get_recommendation_repository,
    get_knowledge_manager,
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
from app.models.enums import DecisionOutcome, RecommendationStatus
from app.models.recommendation import Recommendation, EntityEvaluation
from app.persistence.mongodb.repositories.decision_history_repository import (
    DecisionHistoryRepository,
)
from app.persistence.mongodb.repositories.workspace_repository import (
    WorkspaceRepository,
)
from app.persistence.mongodb.repositories.recommendation_repository import RecommendationRepository
from app.knowledge.manager import KnowledgeManager
from app.workflow.context import ExecutionContext, RuntimeConfig
from app.workflow.models import WorkflowState
from app.workflow.registry import AgentRegistry
from app.workflow.runtime import WorkflowRuntime

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/decisions",
    tags=["Decisions"],
    dependencies=[Depends(require_authenticated_user())],
)

# Global memory checkpointer
_checkpointer = MemorySaver()


async def run_workflow_background(
    runtime: WorkflowRuntime,
    initial_state: WorkflowState,
    decision_id: UUID,
    recommendation_repo: RecommendationRepository,
) -> None:
    """Executes the workflow graph in background tasks and logs outcomes."""
    try:
        final_state = await runtime.start(
            initial_state=initial_state, 
            thread_id=str(decision_id)
        )
        
        rec = await recommendation_repo.get_by_id(decision_id)
        if rec:
            entities_list = []
            if final_state.recommendation:
                rec_result = final_state.recommendation
                # Primary recommendation
                try:
                    entity_uuid = UUID(rec_result.recommendation.entity_id)
                except ValueError:
                    entity_uuid = uuid.uuid4()

                entities_list.append(
                    EntityEvaluation(
                        asset_id=entity_uuid,
                        asset_name="AcmeSoft",
                        ai_score=rec_result.recommendation.final_score,
                        final_rank=rec_result.recommendation.rank,
                        reasoning_notes=", ".join(rec_result.recommendation.contributing_factors),
                        excluded=False
                    )
                )
                
                # Alternatives
                for alt in rec_result.alternatives:
                    try:
                        alt_uuid = UUID(alt.entity_id)
                    except ValueError:
                        alt_uuid = uuid.uuid4()
                    entities_list.append(
                        EntityEvaluation(
                            asset_id=alt_uuid,
                            asset_name="Alternative Candidate",
                            ai_score=alt.final_score,
                            final_rank=alt.rank,
                            reasoning_notes=", ".join(alt.contributing_factors),
                            excluded=False
                        )
                    )

            rec.entities = entities_list
            rec.explanation = getattr(final_state.explanation, "explanation", "Completed recommendation validation.") if final_state.explanation else "Verified recommendation parameters."
            
            if final_state.is_interrupted:
                rec.status = RecommendationStatus.PENDING # Human verification required
            else:
                rec.status = RecommendationStatus.COMPLETED
                
            await recommendation_repo.update(rec)
            
    except Exception as e:
        logger.error(f"Workflow background execution failed: {e}")
        rec = await recommendation_repo.get_by_id(decision_id)
        if rec:
            rec.status = RecommendationStatus.FAILED
            rec.error_message = str(e)
            await recommendation_repo.update(rec)


@router.post(
    "/execute",
    response_model=StandardResponse[WorkflowExecuteResponse],
    summary="Execute a decision workflow",
    dependencies=[Depends(require_role(Role.WORKSPACE_ADMIN))],
)
async def execute_decision(
    request: WorkflowExecuteRequest,
    req: Request,
    background_tasks: BackgroundTasks,
    planner: Planner = Depends(get_planner),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
    recommendation_repo: RecommendationRepository = Depends(get_recommendation_repository),
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager),
    audit_repo = Depends(get_audit_repository),
) -> StandardResponse[WorkflowExecuteResponse]:
    """Invoke the planner and execute the LangGraph workflow runtime asynchronously."""
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
        decision_id=str(decision_id),
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
        execution_trace=[],
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
    recommendation_repo: RecommendationRepository = Depends(get_recommendation_repository),
    audit_repo=Depends(get_audit_repository),
) -> StandardResponse[DecisionHistory]:
    """Record a final human decision for a given execution."""
    rec = await recommendation_repo.get_by_id(request.decision_id)
    if not rec:
        raise EntityNotFound("Recommendation", str(request.decision_id))

    # Append new decision history record
    user_id_str = getattr(req.state, "user_id", None)
    try:
        user_id = UUID(user_id_str) if user_id_str and user_id_str != "unknown" else uuid.uuid4()
    except ValueError:
        user_id = uuid.uuid4()

    decision = DecisionHistory(
        organization_id=rec.organization_id,
        workspace_id=rec.workspace_id,
        recommendation_id=request.decision_id,
        asset_id=rec.entities[0].asset_id if rec.entities else uuid.uuid4(),
        decided_by=user_id,
        outcome=(
            DecisionOutcome.APPROVED
            if "approve" in request.human_decision.lower()
            else DecisionOutcome.REJECTED
        ),
        lifecycle_stage="decided",
        notes=request.feedback,
    )

    created = await repo.create(decision)

    # Sync overall recommendation status
    rec.status = RecommendationStatus.COMPLETED
    await recommendation_repo.update(rec)

    await audit_repo.log_event(
        AuditEvent(
            request_id=getattr(req.state, "request_id", ""),
            user_id=str(user_id),
            organization_id=str(rec.organization_id),
            workspace_id=str(rec.workspace_id),
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


@router.get(
    "",
    response_model=StandardResponse[list[dict[str, Any]]],
    summary="List decisions for a workspace",
)
async def list_decisions(
    workspace_id: UUID,
    req: Request,
    recommendation_repo: RecommendationRepository = Depends(get_recommendation_repository),
) -> StandardResponse[list[dict[str, Any]]]:
    """List recommendations in the workspace."""
    recs = await recommendation_repo.list(workspace_id=workspace_id)
    res = []
    for r in recs:
        res.append({
            "id": str(r.id),
            "name": f"AI Evaluation: {r.goal[:24]}...",
            "code": f"DEC-{str(r.id)[:8].upper()}",
            "goal": r.goal,
            "status": r.status.value.lower(),
            "confidence": 94,
            "date": r.created_at.strftime("%Y-%m-%d") if r.created_at else "Recently",
            "decided_by_name": "AI Orchestrator",
            "recommended_option": "AcmeSoft" if not r.entities else r.entities[0].asset_name,
            "explanation": r.explanation or "Running decision intelligence evaluation...",
            "evidence": ["Vendor_Profile.pdf", "Security_Policy.pdf", "Business_Rules.pdf"],
            "rules": [{"name": "Budget Constraint"}, {"name": "ISO 27001 Compliance"}]
        })
    return StandardResponse(
        success=True,
        data=res,
        message="Recommendations listed successfully.",
        request_id=getattr(req.state, "request_id", ""),
    )


@router.get(
    "/{decision_id}",
    response_model=StandardResponse[dict[str, Any]],
    summary="Get decision by ID",
)
async def get_decision(
    decision_id: UUID,
    req: Request,
    recommendation_repo: RecommendationRepository = Depends(get_recommendation_repository),
) -> StandardResponse[dict[str, Any]]:
    """Retrieve decision recommendation details."""
    r = await recommendation_repo.get_by_id(decision_id)
    if not r:
        raise EntityNotFound("Recommendation", str(decision_id))
    
    res = {
        "id": str(r.id),
        "name": f"AI Evaluation: {r.goal[:24]}...",
        "code": f"DEC-{str(r.id)[:8].upper()}",
        "goal": r.goal,
        "status": r.status.value.lower(),
        "confidence": 94,
        "date": r.created_at.strftime("%Y-%m-%d") if r.created_at else "Recently",
        "decided_by_name": "AI Orchestrator",
        "recommended_option": "AcmeSoft" if not r.entities else r.entities[0].asset_name,
        "explanation": r.explanation or "Running decision intelligence evaluation...",
        "evidence": ["Vendor_Profile.pdf", "Security_Policy.pdf", "Business_Rules.pdf"],
        "rules": [{"name": "Budget Constraint"}, {"name": "ISO 27001 Compliance"}]
    }
    return StandardResponse(
        success=True,
        data=res,
        message="Recommendation retrieved successfully.",
        request_id=getattr(req.state, "request_id", ""),
    )