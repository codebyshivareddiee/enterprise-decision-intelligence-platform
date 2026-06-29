"""Knowledge Layer endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile

from app.api.dependencies import (
    get_audit_repository,
    get_knowledge_asset_repository,
    get_knowledge_manager,
)
from app.api.v1.models.response import StandardResponse
from app.api.v1.models.responses import KnowledgeSearchResponse, KnowledgeUploadResponse
from app.auth.dependencies import (
    require_authenticated_user,
    require_role,
)
from app.auth.models import AuditEvent, Role
from app.core.exceptions import EntityNotFound
from app.knowledge.manager.knowledge_manager import KnowledgeManager
from app.models.enums import AssetContentType, AssetStatus
from app.models.knowledge_asset import KnowledgeAsset
from app.persistence.mongodb.repositories.knowledge_asset_repository import (
    KnowledgeAssetRepository,
)

router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge"],
    dependencies=[Depends(require_authenticated_user())],
)


@router.post(
    "/upload",
    response_model=StandardResponse[KnowledgeUploadResponse],
    summary="Upload a new knowledge document",
    description="Uploads a file, processes it, and indexes it into the vector store.",
    # We use require_role because organization_id is in Form data,
    # making it hard to extract in a generic path-based dependency.
    dependencies=[Depends(require_role(Role.KNOWLEDGE_MANAGER))],
)
async def upload_knowledge(
    request: Request,
    workspace_id: UUID | None = Form(None),
    organization_id: UUID = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...),
    repo: KnowledgeAssetRepository = Depends(get_knowledge_asset_repository),
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager),
    audit_repo=Depends(get_audit_repository),
) -> StandardResponse[KnowledgeUploadResponse]:
    """Upload and index a knowledge asset."""
    content_bytes = await file.read()
    content = content_bytes.decode("utf-8", errors="ignore")

    # Map file content type
    if file.filename and file.filename.endswith(".pdf"):
        content_type = AssetContentType.PDF
    elif file.filename and file.filename.endswith(".md"):
        content_type = AssetContentType.MARKDOWN
    else:
        content_type = AssetContentType.TEXT
 
    import uuid

    dummy_schema_id = uuid.uuid4()
    # In a real app we'd get the user from request context or current_user
    user_id_str = getattr(request.state, "user_id", str(uuid.uuid4()))
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        user_id = uuid.uuid4()
 
    asset = KnowledgeAsset(
        organization_id=organization_id,
        schema_id=dummy_schema_id,
        name=file.filename or "uploaded_document",
        content_type=content_type,
        status=AssetStatus.PENDING,
        raw_content=content,
        user_description=description,
        uploaded_by=user_id,
    )

    asset = await repo.create(asset)

    point_ids = await knowledge_manager.index_asset(asset, available_schemas=[])

    asset.qdrant_point_ids = point_ids
    asset.status = AssetStatus.READY
    await repo.update(asset)

    await audit_repo.log_event(
        AuditEvent(
            request_id=getattr(request.state, "request_id", ""),
            user_id=user_id_str,
            organization_id=str(organization_id),
            workspace_id=str(workspace_id),
            action="upload_knowledge",
            result="success",
        )
    )

    meta = asset.processing_metadata

    upload_response = KnowledgeUploadResponse(
        asset_id=asset.id,
        schema_selected=asset.schema_id,
        chunking_strategy=meta.chunking_strategy if meta else "unknown",
        chunk_profile=meta.chunk_profile if meta else "unknown",
        processing_reasoning=meta.reasoning if meta else "",
        chunks_created=len(point_ids),
    )
    return StandardResponse(
        success=True,
        data=upload_response,
        message="Knowledge asset uploaded successfully.",
        request_id=getattr(request.state, "request_id", ""),
    )


@router.post(
    "/search",
    response_model=StandardResponse[KnowledgeSearchResponse],
    summary="Search knowledge assets",
    dependencies=[Depends(require_role(Role.USER))],
)
async def search_knowledge(
    request: Request,
    organization_id: UUID,
    query: str,
    top_k: int = 10,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager),
) -> StandardResponse[KnowledgeSearchResponse]:
    """Search knowledge across the organization."""
    results = await knowledge_manager.retrieve(
        organization_id=organization_id,
        selected_asset_ids=None,
        query=query,
        top_k=top_k,
    )

    search_response = KnowledgeSearchResponse(
        results=[r.dict() for r in results],
        metadata={"total": len(results)},
    )
    return StandardResponse(
        success=True,
        data=search_response,
        message="Search completed successfully.",
        request_id=getattr(request.state, "request_id", ""),
    )


@router.get(
    "/assets",
    response_model=StandardResponse[list[KnowledgeAsset]],
    summary="List knowledge assets",
)
async def list_assets(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    repo: KnowledgeAssetRepository = Depends(get_knowledge_asset_repository),
) -> StandardResponse[list[KnowledgeAsset]]:
    """List knowledge assets."""
    # current_user.organization_id is not available on User model (it's in memberships)
    # So we'll list all assets the user has access to, or just fetch them.
    # For now, list all globally (or extract org from request context).
    org_id_str = getattr(request.state, "organization_id", None)
    if org_id_str and org_id_str != "unknown":
        org_id = UUID(org_id_str)
        assets = await repo.list(organization_id=org_id, skip=skip, limit=limit)
    else:
        assets = await repo.list(skip=skip, limit=limit)

    return StandardResponse(
        success=True,
        data=assets,
        message="Knowledge assets retrieved successfully.",
        request_id=getattr(request.state, "request_id", ""),
    )


@router.get(
    "/assets/{asset_id}",
    response_model=StandardResponse[KnowledgeAsset],
    summary="Get a knowledge asset",
)
async def get_asset(
    asset_id: UUID,
    request: Request,
    repo: KnowledgeAssetRepository = Depends(get_knowledge_asset_repository),
) -> StandardResponse[KnowledgeAsset]:
    """Get knowledge asset by ID."""
    asset = await repo.get_by_id(asset_id)
    if not asset:
        raise EntityNotFound("KnowledgeAsset", str(asset_id))
    return StandardResponse(
        success=True,
        data=asset,
        message="Knowledge asset retrieved successfully.",
        request_id=getattr(request.state, "request_id", ""),
    )
