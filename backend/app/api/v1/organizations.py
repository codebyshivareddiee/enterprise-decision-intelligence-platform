"""Organizations endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_organization_repository, get_audit_repository
from app.core.exceptions import EntityNotFound
from app.models.organization import Organization
from app.persistence.mongodb.repositories.organization_repository import OrganizationRepository
from app.auth.dependencies import require_authenticated_user, require_organization_access, require_role
from app.auth.permissions import Permission
from app.auth.models import Role
from app.api.v1.models.response import StandardResponse

router = APIRouter(
    prefix="/organizations", 
    tags=["Organizations"],
    dependencies=[Depends(require_authenticated_user())]
)


@router.post(
    "",
    response_model=StandardResponse[Organization],
    summary="Create a new organization",
    description="Registers a new organization within the platform.",
    status_code=201,
    # Only Platform Admin or Organization Admin can create orgs
    dependencies=[Depends(require_role(Role.PLATFORM_ADMIN))],
)
async def create_organization(
    org: Organization,
    request: Request,
    repo: OrganizationRepository = Depends(get_organization_repository),
    audit_repo = Depends(get_audit_repository),
) -> StandardResponse[Organization]:
    """Create organization."""
    created = await repo.create(org)
    
    from app.auth.models import AuditEvent
    user_id_str = getattr(request.state, "user_id", "")
    await audit_repo.log_event(AuditEvent(
        request_id=getattr(request.state, "request_id", ""),
        user_id=user_id_str if user_id_str else None,
        organization_id=str(created.id),
        action="create_organization",
        result="success"
    ))
    
    return StandardResponse(
        success=True,
        data=created,
        message="Organization created successfully.",
        request_id=getattr(request.state, "request_id", ""),
    )


@router.get(
    "",
    response_model=StandardResponse[list[Organization]],
    summary="List organizations",
    description="Returns a paginated list of all organizations.",
)
async def list_organizations(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    repo: OrganizationRepository = Depends(get_organization_repository),
) -> StandardResponse[list[Organization]]:
    """List organizations."""
    orgs = await repo.list(skip=skip, limit=limit)
    return StandardResponse(
        success=True,
        data=orgs,
        message="Organizations retrieved successfully.",
        request_id=getattr(request.state, "request_id", ""),
    )


@router.get(
    "/{organization_id}",
    response_model=StandardResponse[Organization],
    summary="Get an organization",
    description="Retrieves a specific organization by its UUID.",
)
async def get_organization(
    organization_id: UUID,
    request: Request,
    repo: OrganizationRepository = Depends(get_organization_repository),
) -> StandardResponse[Organization]:
    """Get organization by ID."""
    org = await repo.get_by_id(organization_id)
    if not org:
        raise EntityNotFound("Organization", str(organization_id))
    return StandardResponse(
        success=True,
        data=org,
        message="Organization retrieved successfully.",
        request_id=getattr(request.state, "request_id", ""),
    )


@router.patch(
    "/{organization_id}",
    response_model=StandardResponse[Organization],
    summary="Update an organization",
    description="Partially updates an existing organization.",
    dependencies=[Depends(require_organization_access(Permission.MANAGE_ORGANIZATIONS))],
)
async def update_organization(
    organization_id: UUID,
    org_update: Organization,
    request: Request,
    repo: OrganizationRepository = Depends(get_organization_repository),
) -> StandardResponse[Organization]:
    """Update organization."""
    if organization_id != org_update.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="ID in path must match ID in body.")
    
    updated_org = await repo.update(org_update)
    if not updated_org:
        raise EntityNotFound("Organization", str(organization_id))
    return StandardResponse(
        success=True,
        data=updated_org,
        message="Organization updated successfully.",
        request_id=getattr(request.state, "request_id", ""),
    )
