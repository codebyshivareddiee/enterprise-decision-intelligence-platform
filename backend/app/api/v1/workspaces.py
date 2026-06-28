"""Workspaces endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_workspace_repository
from app.core.exceptions import EntityNotFound
from app.models.workspace import Workspace
from app.persistence.mongodb.repositories.workspace_repository import WorkspaceRepository
from app.auth.dependencies import get_current_user, require_permission
from app.auth.permissions import Permission

router = APIRouter(
    tags=["Workspaces"],
    dependencies=[Depends(get_current_user)]
)


@router.post(
    "/workspaces",
    response_model=Workspace,
    summary="Create a new workspace",
    description="Registers a new workspace under an organization.",
    status_code=201,
    dependencies=[Depends(require_permission(Permission.MANAGE_WORKSPACES))],
)
async def create_workspace(
    workspace: Workspace,
    repo: WorkspaceRepository = Depends(get_workspace_repository),
) -> Workspace:
    """Create workspace."""
    return await repo.create(workspace)


@router.get(
    "/workspaces/{workspace_id}",
    response_model=Workspace,
    summary="Get a workspace",
    description="Retrieves a specific workspace by its UUID.",
)
async def get_workspace(
    workspace_id: UUID,
    repo: WorkspaceRepository = Depends(get_workspace_repository),
) -> Workspace:
    """Get workspace by ID."""
    ws = await repo.get_by_id(workspace_id)
    if not ws:
        raise EntityNotFound("Workspace", str(workspace_id))
    return ws


@router.patch(
    "/workspaces/{workspace_id}",
    response_model=Workspace,
    summary="Update a workspace",
    description="Partially updates an existing workspace.",
    dependencies=[Depends(require_permission(Permission.MANAGE_WORKSPACE))],
)
async def update_workspace(
    workspace_id: UUID,
    ws_update: Workspace,
    repo: WorkspaceRepository = Depends(get_workspace_repository),
) -> Workspace:
    """Update workspace."""
    if workspace_id != ws_update.id:
        raise HTTPException(status_code=400, detail="ID in path must match ID in body.")
    
    updated_ws = await repo.update(ws_update)
    if not updated_ws:
        raise EntityNotFound("Workspace", str(workspace_id))
    return updated_ws


@router.get(
    "/organizations/{org_id}/workspaces",
    response_model=list[Workspace],
    summary="List workspaces for organization",
    description="Returns all workspaces belonging to the specified organization.",
)
async def list_org_workspaces(
    org_id: UUID,
    repo: WorkspaceRepository = Depends(get_workspace_repository),
) -> list[Workspace]:
    """List workspaces for a specific organization."""
    return await repo.list(organization_id=org_id, limit=1000)
