"""Business Rules endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.dependencies import (
    get_audit_repository,
    get_workspace_repository,
)
from app.api.v1.models.requests import BusinessRuleCreateRequest
from app.api.v1.models.responses import BusinessRuleResponse
from app.api.v1.models.response import StandardResponse
from app.auth.dependencies import (
    require_authenticated_user,
    require_workspace_access,
)
from app.auth.models import User
from app.auth.permissions import Permission
from app.core.exceptions import EntityNotFound
from app.models.business_rule import BusinessRule
from app.persistence.mongodb.repositories.business_rule_repository import (
    BusinessRuleRepository,
)
from app.persistence.mongodb.repositories.workspace_repository import (
    WorkspaceRepository,
)
from app.api.dependencies import get_db

async def get_business_rule_repository(db=Depends(get_db)) -> BusinessRuleRepository:
    return BusinessRuleRepository(db)

router = APIRouter(
    tags=["Business Rules"], dependencies=[Depends(require_authenticated_user())]
)

@router.get(
    "/workspaces/{workspace_id}/rules",
    response_model=StandardResponse[list[BusinessRuleResponse]],
    summary="List business rules for workspace",
)
async def list_workspace_rules(
    workspace_id: UUID,
    request: Request,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
    rule_repo: BusinessRuleRepository = Depends(get_business_rule_repository),
) -> StandardResponse[list[BusinessRuleResponse]]:
    workspace = await workspace_repo.get_by_id(workspace_id)
    if not workspace:
        raise EntityNotFound("Workspace", str(workspace_id))

    rules = await rule_repo.list(
        organization_id=workspace.organization_id,
        workspace_id=workspace_id,
        limit=1000,
    )
    
    return StandardResponse(
        success=True,
        data=[BusinessRuleResponse.model_validate(r.model_dump()) for r in rules],
        message="Business rules retrieved successfully.",
        request_id=getattr(request.state, "request_id", ""),
    )

@router.post(
    "/workspaces/{workspace_id}/rules",
    response_model=StandardResponse[BusinessRuleResponse],
    summary="Create a new business rule",
    status_code=201,
    dependencies=[Depends(require_workspace_access(Permission.MANAGE_WORKSPACE))],
)
async def create_business_rule(
    workspace_id: UUID,
    rule_req: BusinessRuleCreateRequest,
    request: Request,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
    rule_repo: BusinessRuleRepository = Depends(get_business_rule_repository),
    audit_repo=Depends(get_audit_repository),
) -> StandardResponse[BusinessRuleResponse]:
    workspace = await workspace_repo.get_by_id(workspace_id)
    if not workspace:
        raise EntityNotFound("Workspace", str(workspace_id))

    rule = BusinessRule(
        organization_id=workspace.organization_id,
        workspace_id=workspace_id,
        name=rule_req.name,
        description=rule_req.description,
        rule_type=rule_req.rule_type,
        conditions=rule_req.conditions,
        is_active=rule_req.is_active,
        weight=rule_req.weight,
        priority=rule_req.priority,
    )

    created = await rule_repo.create(rule)

    from app.auth.models import AuditEvent
    user_id_str = getattr(request.state, "user_id", "")
    await audit_repo.log_event(
        AuditEvent(
            request_id=getattr(request.state, "request_id", ""),
            user_id=user_id_str if user_id_str else None,
            organization_id=str(created.organization_id),
            workspace_id=str(created.workspace_id),
            action="create_business_rule",
            result="success",
        )
    )

    return StandardResponse(
        success=True,
        data=BusinessRuleResponse.model_validate(created.model_dump()),
        message="Business rule created successfully.",
        request_id=getattr(request.state, "request_id", ""),
    )

@router.delete(
    "/workspaces/{workspace_id}/rules/{rule_id}",
    response_model=StandardResponse[bool],
    summary="Delete a business rule",
    dependencies=[Depends(require_workspace_access(Permission.MANAGE_WORKSPACE))],
)
async def delete_business_rule(
    workspace_id: UUID,
    rule_id: UUID,
    request: Request,
    rule_repo: BusinessRuleRepository = Depends(get_business_rule_repository),
    audit_repo=Depends(get_audit_repository),
) -> StandardResponse[bool]:
    rule = await rule_repo.get_by_id(rule_id)
    if not rule or rule.workspace_id != workspace_id:
        raise EntityNotFound("BusinessRule", str(rule_id))

    deleted = await rule_repo.delete(rule_id)
    
    from app.auth.models import AuditEvent
    user_id_str = getattr(request.state, "user_id", "")
    await audit_repo.log_event(
        AuditEvent(
            request_id=getattr(request.state, "request_id", ""),
            user_id=user_id_str if user_id_str else None,
            organization_id=str(rule.organization_id),
            workspace_id=str(rule.workspace_id),
            action="delete_business_rule",
            result="success",
        )
    )

    return StandardResponse(
        success=True,
        data=deleted,
        message="Business rule deleted successfully.",
        request_id=getattr(request.state, "request_id", ""),
    )
