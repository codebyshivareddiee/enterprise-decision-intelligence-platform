"""Workspaces endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.dependencies import (
    get_audit_repository,
    get_workspace_repository,
    get_knowledge_asset_repository,
)
from app.api.v1.models.requests import WorkspaceCreateRequest, WorkspaceKnowledgeAttachRequest
from app.api.v1.models.responses import WorkspaceResponse
from app.api.v1.models.response import StandardResponse
from app.auth.dependencies import (
    require_authenticated_user,
    require_role,
    require_workspace_access,
)
from app.auth.models import Role, User
from app.auth.permissions import Permission
from app.core.exceptions import EntityNotFound
from app.models.workspace import Workspace
from app.persistence.mongodb.repositories.workspace_repository import (
    WorkspaceRepository,
)
from app.persistence.mongodb.repositories.knowledge_asset_repository import (
    KnowledgeAssetRepository,
)

router = APIRouter(
    tags=["Workspaces"], dependencies=[Depends(require_authenticated_user())]
)


@router.post(
    "/workspaces",
    response_model=StandardResponse[WorkspaceResponse],
    summary="Create a new workspace",
    description="Registers a new workspace under the user's organization.",
    status_code=201,
)
async def create_workspace(
    workspace_req: WorkspaceCreateRequest,
    request: Request,
    current_user: User = Depends(require_authenticated_user()),
    repo: WorkspaceRepository = Depends(get_workspace_repository),
    audit_repo=Depends(get_audit_repository),
) -> StandardResponse[WorkspaceResponse]:
    """Create workspace."""
    if not current_user.memberships:
        raise HTTPException(
            status_code=403,
            detail="You must belong to an organization to create a workspace."
        )

    if not any(m.role == Role.PLATFORM_ADMIN for m in current_user.memberships) and not any(m.role == Role.ORGANIZATION_ADMIN for m in current_user.memberships):
        raise HTTPException(
            status_code=403,
            detail=f"Requires role {Role.ORGANIZATION_ADMIN.value}"
        )

    org_id = current_user.memberships[0].organization_id

    workspace = Workspace(
        organization_id=org_id,
        owner_id=current_user.id,
        name=workspace_req.name,
        description=workspace_req.description,
        goal=workspace_req.goal,
        success_metrics=workspace_req.success_metrics,
        decision_points=workspace_req.decision_points,
    )

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
        data=WorkspaceResponse.model_validate(created.model_dump()),
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


@router.post(
    "/workspaces/{workspace_id}/knowledge",
    response_model=StandardResponse[WorkspaceResponse],
    summary="Attach knowledge assets to a workspace",
    description="Attaches specified organization knowledge assets to the workspace without duplicating them.",
    dependencies=[Depends(require_workspace_access(Permission.MANAGE_WORKSPACE))],
)
async def attach_knowledge_assets(
    workspace_id: UUID,
    attach_req: WorkspaceKnowledgeAttachRequest,
    request: Request,
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
    asset_repo: KnowledgeAssetRepository = Depends(get_knowledge_asset_repository),
    audit_repo=Depends(get_audit_repository),
) -> StandardResponse[WorkspaceResponse]:
    """Attach knowledge assets to workspace."""
    # 1. Fetch the workspace
    workspace = await workspace_repo.get_by_id(workspace_id)
    if not workspace:
        raise EntityNotFound("Workspace", str(workspace_id))
    
    # 2. Fetch and validate all assets
    if attach_req.asset_ids:
        # get_by_ids needs list of strings, so we convert UUIDs
        asset_id_strs = [str(aid) for aid in attach_req.asset_ids]
        # pyrefly: ignore [bad-argument-type]
        assets = await asset_repo.get_by_ids(workspace.organization_id, asset_id_strs)
        
        found_asset_ids = {str(a.id) for a in assets}
        missing_ids = [aid for aid in asset_id_strs if aid not in found_asset_ids]
        
        if missing_ids:
            raise HTTPException(
                status_code=400,
                detail=f"The following assets do not exist or belong to another organization: {', '.join(missing_ids)}"
            )

    # 3. Update the workspace explicitly avoiding duplicates
    current_ids = {str(aid) for aid in workspace.selected_knowledge_asset_ids} if workspace.selected_knowledge_asset_ids else set()
    new_ids = [aid for aid in attach_req.asset_ids if str(aid) not in current_ids]
    if new_ids:
        workspace.selected_knowledge_asset_ids.extend(new_ids)
        updated_ws = await workspace_repo.update(workspace)
        if not updated_ws:
            raise HTTPException(status_code=500, detail="Failed to update workspace")
        workspace = updated_ws

        # Audit log
        user_id_str = getattr(request.state, "user_id", "")
        from app.auth.models import AuditEvent
        await audit_repo.log_event(
            AuditEvent(
                request_id=getattr(request.state, "request_id", ""),
                user_id=user_id_str if user_id_str else None,
                organization_id=str(workspace.organization_id),
                workspace_id=str(workspace.id),
                action="attach_knowledge_assets",
                result="success",
            )
        )

    return StandardResponse(
        success=True,
        data=WorkspaceResponse.model_validate(workspace.model_dump()),
        message=f"{len(new_ids)} knowledge assets attached successfully.",
        request_id=getattr(request.state, "request_id", ""),
    )

