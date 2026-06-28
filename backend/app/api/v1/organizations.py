"""Organizations endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_organization_repository
from app.core.exceptions import EntityNotFound
from app.models.organization import Organization
from app.persistence.mongodb.repositories.organization_repository import OrganizationRepository

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.post(
    "",
    response_model=Organization,
    summary="Create a new organization",
    description="Registers a new organization within the platform.",
    status_code=201,
)
async def create_organization(
    org: Organization,
    repo: OrganizationRepository = Depends(get_organization_repository),
) -> Organization:
    """Create organization."""
    return await repo.create(org)


@router.get(
    "",
    response_model=list[Organization],
    summary="List organizations",
    description="Returns a paginated list of all organizations.",
)
async def list_organizations(
    skip: int = 0,
    limit: int = 100,
    repo: OrganizationRepository = Depends(get_organization_repository),
) -> list[Organization]:
    """List organizations."""
    return await repo.list(skip=skip, limit=limit)


@router.get(
    "/{org_id}",
    response_model=Organization,
    summary="Get an organization",
    description="Retrieves a specific organization by its UUID.",
)
async def get_organization(
    org_id: UUID,
    repo: OrganizationRepository = Depends(get_organization_repository),
) -> Organization:
    """Get organization by ID."""
    org = await repo.get_by_id(org_id)
    if not org:
        raise EntityNotFound("Organization", str(org_id))
    return org


@router.patch(
    "/{org_id}",
    response_model=Organization,
    summary="Update an organization",
    description="Partially updates an existing organization.",
)
async def update_organization(
    org_id: UUID,
    org_update: Organization,
    repo: OrganizationRepository = Depends(get_organization_repository),
) -> Organization:
    """Update organization."""
    if org_id != org_update.id:
        raise HTTPException(status_code=400, detail="ID in path must match ID in body.")
    
    updated_org = await repo.update(org_update)
    if not updated_org:
        raise EntityNotFound("Organization", str(org_id))
    return updated_org
