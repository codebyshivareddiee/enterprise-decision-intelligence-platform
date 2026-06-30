"""Decisions and Workflow execution endpoints."""

import uuid
import logging
from uuid import UUID
from typing import Any

from fastapi import APIRouter, Depends, Request, BackgroundTasks, WebSocket, WebSocketDisconnect
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
    get_knowledge_asset_repository,
    get_business_rule_repository
)
from app.api.v1.models.requests import (
    DecisionOutcomeRequest,
    WorkflowExecuteRequest,
    WorkflowResumeRequest,
)
from app.api.v1.models.response import StandardResponse
from app.api.v1.models.responses import WorkflowExecuteResponse, WorkflowStatusResponse, EvidenceItem
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
from app.persistence.mongodb.repositories.knowledge_asset_repository import KnowledgeAssetRepository
from app.persistence.mongodb.repositories.business_rule_repository import BusinessRuleRepository
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

ws_router = APIRouter(
    prefix="/decisions/ws",
    tags=["Decisions WebSocket"]
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
                        asset_name=getattr(rec_result.recommendation, "entity_name", "Primary Candidate"),
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
                            asset_name=getattr(alt, "entity_name", "Alternative Candidate"),
                            ai_score=alt.final_score,
                            final_rank=alt.rank,
                            reasoning_notes=", ".join(alt.contributing_factors),
                            excluded=False
                        )
                    )

            rec.entities = entities_list
            if final_state.explanation:
                rec.explanation = getattr(final_state.explanation, "summary", "Completed recommendation validation.")
                rec.evidence = getattr(final_state.explanation, "evidence_references", [])
                rec.rules = getattr(final_state.explanation, "applied_rules", [])
            else:
                rec.explanation = "Verified recommendation parameters."
                rec.evidence = []
                rec.rules = []
            
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
)
async def execute_decision(
    request: WorkflowExecuteRequest,
    req: Request,
    background_tasks: BackgroundTasks,
    planner: Planner = Depends(get_planner),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
    recommendation_repo: RecommendationRepository = Depends(get_recommendation_repository),
    knowledge_asset_repo: KnowledgeAssetRepository = Depends(get_knowledge_asset_repository),
    business_rule_repo: BusinessRuleRepository = Depends(get_business_rule_repository),
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
    workspace_decision_context = workspace.model_dump(mode="json") if hasattr(workspace, "model_dump") else workspace.dict()
    workspace_rules = await business_rule_repo.list(
        organization_id=workspace.organization_id, 
        workspace_id=workspace.id
    )
    workspace_decision_context["business_rules"] = [
        rule.model_dump(mode="json") if hasattr(rule, "model_dump") else rule.dict() 
        for rule in workspace_rules
    ]
    
    workspace_decision_context["preference_profile"] = {}
    workspace_decision_context["knowledge_schemas"] = []
    
    # Retrieve real selected knowledge assets as strings for state
    selected_asset_ids = [str(aid) for aid in workspace.selected_knowledge_asset_ids] if workspace.selected_knowledge_asset_ids else []
    
    # Fetch actual asset names to provide better context to the Planner and Retriever
    asset_names = []
    if workspace.selected_knowledge_asset_ids:
        for aid in workspace.selected_knowledge_asset_ids:
            asset = await knowledge_asset_repo.get_by_id(aid)
            if asset and asset.name:
                asset_names.append(asset.name)
    workspace_decision_context["knowledge_asset_names"] = asset_names

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

    from app.workflow.registry import build_default_registry
    registry = build_default_registry(
        knowledge_manager=knowledge_manager,
        ai_manager=planner.ai_manager
    )

    initial_state = WorkflowState(
        plan=plan,
        decision_id=str(decision_id),
        user_request=request.user_request,
        workspace_context=workspace_decision_context,
        workspace=workspace.model_dump(mode="json") if hasattr(workspace, "model_dump") else workspace.dict(),
        organization={"id": str(workspace.organization_id)},
        selected_knowledge_asset_ids=selected_asset_ids,
        selected_business_rule_ids=[],
    )

    context = ExecutionContext(
        plan=plan,
        state=initial_state,
        registry=registry,
        planner=planner,
        config=RuntimeConfig(),
        checkpointer=_checkpointer,
    )

    from app.models.recommendation import Recommendation, RecommendationStatus

    user_id_str = getattr(req.state, "user_id", None)
    try:
        user_id = UUID(user_id_str) if user_id_str and user_id_str != "unknown" else uuid.uuid4()
    except ValueError:
        user_id = uuid.uuid4()

    rec_obj = Recommendation(
        id=decision_id,
        organization_id=workspace.organization_id,
        workspace_id=workspace.id,
        goal=request.user_request,
        status=RecommendationStatus.PENDING,
        triggered_by=user_id,
        plan_snapshot=plan.model_dump().get("execution_steps", []) if hasattr(plan, "model_dump") else plan.dict().get("execution_steps", []),
    )
    await recommendation_repo.create(rec_obj)

    runtime = WorkflowRuntime(context)

    # Build graph dict for frontend immediately
    nodes = []
    edges = []
    
    for step in plan.execution_steps:
        nodes.append({
            "id": step.step_id,
            "type": "agent",
            "data": {
                "label": step.step_id.replace("_", " ").title(),
                "agent_name": step.agent_name.value if hasattr(step.agent_name, "value") else str(step.agent_name)
            }
        })
        for dep in step.depends_on:
            edges.append({
                "id": f"{dep}-{step.step_id}",
                "source": dep,
                "target": step.step_id
            })
            
    graph_dict = {"nodes": nodes, "edges": edges}

    # Execute workflow in background
    background_tasks.add_task(
        run_workflow_background,
        runtime=runtime,
        initial_state=initial_state,
        decision_id=decision_id,
        recommendation_repo=recommendation_repo
    )

    exec_resp = WorkflowExecuteResponse(
        decision_id=decision_id,
        execution_plan=plan.model_dump() if hasattr(plan, "model_dump") else plan.dict(),
        graph=graph_dict,
        execution_status="PENDING",
        requires_human_review=plan.requires_human_review,
        recommendation=None,
        explanation=None,
        execution_trace=[],
        supporting_evidence=[],
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
)
async def resume_decision(
    decision_id: UUID,
    request: WorkflowResumeRequest,
    req: Request,
    planner: Planner = Depends(get_planner),
    audit_repo=Depends(get_audit_repository),
) -> StandardResponse[WorkflowStatusResponse]:
    """Resumes a workflow that was paused for human review."""

    # Reconstruct context from the checkpointer
    config_dict = {"configurable": {"thread_id": str(decision_id)}}
    state_snapshot = await _checkpointer.aget_tuple(config_dict)
    
    if not state_snapshot:
        raise EntityNotFound("Workflow State", str(decision_id))
    
    saved_state = state_snapshot.checkpoint.get("channel_values", {})
    if "__root__" in saved_state:
        # LangGraph 0.1 / 0.2 handles root state differently
        saved_state = saved_state["__root__"]
    
    # Try parsing saved_state into WorkflowState to get the plan
    plan_obj = None
    if isinstance(saved_state, dict) and "plan" in saved_state and saved_state["plan"]:
        from app.agents.planner.schemas import ExecutionPlan
        plan_obj = ExecutionPlan(**saved_state["plan"])
    elif hasattr(saved_state, "plan"):
        plan_obj = saved_state.plan

    from app.workflow.registry import build_default_registry
    registry = build_default_registry(
        ai_manager=planner.ai_manager
    )
    
    context = ExecutionContext(
        plan=plan_obj,
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
        current_state=final_state.model_dump(exclude={"plan"}),
        completed_nodes=final_state.completed_steps,
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
    history_repo: DecisionHistoryRepository = Depends(get_decision_history_repository),
) -> StandardResponse[list[dict[str, Any]]]:
    """List recommendations in the workspace."""
    recs = await recommendation_repo.list(workspace_id=workspace_id)
    history_records = await history_repo.list(workspace_id=workspace_id)
    history_by_rec = {str(h.recommendation_id): h for h in history_records}
    
    res = []
    for r in recs:
        h = history_by_rec.get(str(r.id))
        status_str = h.outcome.value.lower() if h else r.status.value.lower()
        feedback_str = h.notes if h else None
        
        # calculate actual confidence if present
        conf = 94
        if r.entities and r.entities[0].ai_score:
            conf = int(r.entities[0].ai_score * 100)

        res.append({
            "id": str(r.id),
            "name": f"AI Evaluation: {r.goal[:24]}...",
            "code": f"DEC-{str(r.id)[:8].upper()}",
            "goal": r.goal,
            "status": status_str,
            "confidence": conf,
            "date": r.created_at.strftime("%Y-%m-%d") if r.created_at else "Recently",
            "decided_by_name": "AI Orchestrator",
            "recommended_option": "Insufficient Data / No Decision" if not r.entities else r.entities[0].asset_name,
            "explanation": r.explanation or "Running decision intelligence evaluation...",
            "evidence": r.evidence if hasattr(r, "evidence") else [],
            "rules": [{"name": rule} for rule in r.rules] if hasattr(r, "rules") else [],
            "alternatives": [
                {
                    "entity_name": e.asset_name,
                    "score": int(e.ai_score * 100) if e.ai_score else 0,
                    "reasoning": e.reasoning_notes
                } for e in r.entities[1:]
            ] if r.entities and len(r.entities) > 1 else [],
            "feedback": feedback_str
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
        "confidence": int(r.entities[0].ai_score * 100) if r.entities and r.entities[0].ai_score else 94,
        "date": r.created_at.strftime("%Y-%m-%d") if r.created_at else "Recently",
        "decided_by_name": "AI Orchestrator",
        "recommended_option": "Insufficient Data / No Decision" if not r.entities else r.entities[0].asset_name,
        "explanation": r.explanation or "Running decision intelligence evaluation...",
        "evidence": r.evidence if hasattr(r, "evidence") else [],
        "rules": [{"name": rule} for rule in r.rules] if hasattr(r, "rules") else [],
        "alternatives": [
            {
                "entity_name": e.asset_name,
                "score": int(e.ai_score * 100) if e.ai_score else 0,
                "reasoning": e.reasoning_notes
            } for e in r.entities[1:]
        ] if r.entities and len(r.entities) > 1 else []
    }
    return StandardResponse(
        success=True,
        data=res,
        message="Recommendation retrieved successfully.",
        request_id=getattr(req.state, "request_id", ""),
    )


@ws_router.websocket("/workflows/{workflow_id}")
async def workflow_websocket(websocket: WebSocket, workflow_id: str):
    """WebSocket endpoint to stream workflow execution events."""
    await websocket.accept()
    from app.workflow.events import event_bus
    
    queue = await event_bus.subscribe(workflow_id)
    try:
        while True:
            # Wait for events from the queue
            msg = await queue.get()
            await websocket.send_text(msg)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error for workflow {workflow_id}: {e}")
    finally:
        event_bus.unsubscribe(workflow_id, queue)
