"""Workspaces endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.dependencies import get_audit_repository, get_workspace_repository
from app.api.v1.models.response import StandardResponse
from app.auth.dependencies import (
    require_authenticated_user,
    require_role,
    require_workspace_access,
)
from app.auth.models import Role
from app.auth.permissions import Permission
from app.core.exceptions import EntityNotFound
from app.models.workspace import Workspace
from app.persistence.mongodb.repositories.workspace_repository import (
    WorkspaceRepository,
)

router = APIRouter(
    tags=["Workspaces"], dependencies=[Depends(require_authenticated_user())]
)


@router.post(
    "/workspaces",
    response_model=StandardResponse[Workspace],
    summary="Create a new workspace",
    description="Registers a new workspace under an organization.",
    status_code=201,
    dependencies=[Depends(require_role(Role.ORGANIZATION_ADMIN))],
)
async def create_workspace(
    workspace: Workspace,
    request: Request,
    repo: WorkspaceRepository = Depends(get_workspace_repository),
    audit_repo=Depends(get_audit_repository),
) -> StandardResponse[Workspace]:
    """Create workspace."""
    created = await repo.create(workspace)

    from app.auth.models import AuditEvent

    user_id_str = getattr(request.state, "user_id", "")
    await audit_repo.log_event(
        AuditEvent(
            request_id=getattr(request.state, "request_id", ""),
            user_id=user_id_str if user_id_str else None,
            organization_id=str(created.organization_id),
            workspace_id=str(created.id),
            action="create_workspace",
            result="success",
        )
    )

    return StandardResponse(
        success=True,
        data=created,
        message="Workspace created successfully.",
        request_id=getattr(request.state, "request_id", ""),
    )


@router.get(
    "/workspaces/{workspace_id}",
    response_model=StandardResponse[Workspace],
    summary="Get a workspace",
    description="Retrieves a specific workspace by its UUID.",
)
async def get_workspace(
    workspace_id: UUID,
    request: Request,
    repo: WorkspaceRepository = Depends(get_workspace_repository),
) -> StandardResponse[Workspace]:
    """Get workspace by ID."""
    ws = await repo.get_by_id(workspace_id)
    if not ws:
        raise EntityNotFound("Workspace", str(workspace_id))
    return StandardResponse(
        success=True,
        data=ws,
        message="Workspace retrieved successfully.",
        request_id=getattr(request.state, "request_id", ""),
    )


@router.patch(
    "/workspaces/{workspace_id}",
    response_model=StandardResponse[Workspace],
    summary="Update a workspace",
    description="Partially updates an existing workspace.",
    dependencies=[Depends(require_workspace_access(Permission.MANAGE_WORKSPACE))],
)
async def update_workspace(
    workspace_id: UUID,
    ws_update: Workspace,
    request: Request,
    repo: WorkspaceRepository = Depends(get_workspace_repository),
) -> StandardResponse[Workspace]:
    """Update workspace."""
    if workspace_id != ws_update.id:
        raise HTTPException(status_code=400, detail="ID in path must match ID in body.")

    updated_ws = await repo.update(ws_update)
    if not updated_ws:
        raise EntityNotFound("Workspace", str(workspace_id))
    return StandardResponse(
        success=True,
        data=updated_ws,
        message="Workspace updated successfully.",
        request_id=getattr(request.state, "request_id", ""),
    )


@router.get(
    "/organizations/{organization_id}/workspaces",
    response_model=StandardResponse[list[Workspace]],
    summary="List workspaces for organization",
    description="Returns all workspaces belonging to the specified organization.",
)
async def list_org_workspaces(
    organization_id: UUID,
    request: Request,
    repo: WorkspaceRepository = Depends(get_workspace_repository),
) -> StandardResponse[list[Workspace]]:
    """List workspaces for a specific organization."""
    workspaces = await repo.list(organization_id=organization_id, limit=1000)
    return StandardResponse(
        success=True,
        data=workspaces,
        message="Workspaces retrieved successfully.",
        request_id=getattr(request.state, "request_id", ""),
    )
