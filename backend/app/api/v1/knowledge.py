"""Knowledge Layer endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.dependencies import get_knowledge_asset_repository, get_knowledge_manager
from app.api.v1.models.responses import KnowledgeSearchResponse, KnowledgeUploadResponse
from app.core.exceptions import EntityNotFound
from app.knowledge.manager.knowledge_manager import KnowledgeManager
from app.models.enums import AssetContentType, AssetStatus
from app.models.knowledge_asset import KnowledgeAsset
from app.persistence.mongodb.repositories.knowledge_asset_repository import KnowledgeAssetRepository
from app.models.knowledge_schema import KnowledgeSchema
from app.auth.dependencies import get_current_user, require_permission
from app.auth.permissions import Permission

router = APIRouter(
    prefix="/knowledge", 
    tags=["Knowledge"],
    dependencies=[Depends(get_current_user)]
)


@router.post(
    "/upload",
    response_model=KnowledgeUploadResponse,
    summary="Upload a new knowledge document",
    description="Uploads a file, processes it, and indexes it into the vector store.",
    dependencies=[Depends(require_permission(Permission.UPLOAD_KNOWLEDGE))],
)
async def upload_knowledge(
    workspace_id: UUID = Form(...),
    organization_id: UUID = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...),
    repo: KnowledgeAssetRepository = Depends(get_knowledge_asset_repository),
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager),
) -> KnowledgeUploadResponse:
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

    # Create the KnowledgeAsset
    # A default or matched schema will be applied during processing.
    # For now, pass a dummy schema ID because it's required by the model. 
    # The DocumentProcessor will update it.
    import uuid
    dummy_schema_id = uuid.uuid4()
    dummy_user_id = uuid.uuid4()

    asset = KnowledgeAsset(
        organization_id=organization_id,
        schema_id=dummy_schema_id,
        name=file.filename or "uploaded_document",
        content_type=content_type,
        status=AssetStatus.PENDING,
        raw_content=content,
        user_description=description,
        uploaded_by=dummy_user_id, # In a real app, from request context
    )
    
    # Save initially
    asset = await repo.create(asset)
    
    # Process and index
    # Provide an empty list of schemas for now if we don't fetch them
    # In a full implementation, we'd fetch all KnowledgeSchemas for the org.
    point_ids = await knowledge_manager.index_asset(asset, available_schemas=[])
    
    asset.qdrant_point_ids = point_ids
    asset.status = AssetStatus.READY
    await repo.update(asset)
    
    # Extract metadata for response
    meta = asset.processing_metadata
    
    return KnowledgeUploadResponse(
        asset_id=asset.id,
        schema_selected=asset.schema_id,
        chunking_strategy=meta.chunking_strategy if meta else "unknown",
        chunk_profile=meta.chunk_profile if meta else "unknown",
        processing_reasoning=meta.reasoning if meta else "",
        chunks_created=len(point_ids),
    )


@router.post(
    "/search",
    response_model=KnowledgeSearchResponse,
    summary="Search knowledge assets",
    dependencies=[Depends(require_permission(Permission.SEARCH_KNOWLEDGE))],
)
async def search_knowledge(
    organization_id: UUID,
    query: str,
    top_k: int = 10,
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager),
) -> KnowledgeSearchResponse:
    """Search knowledge across the organization."""
    results = await knowledge_manager.retrieve(
        organization_id=organization_id,
        selected_asset_ids=None,
        query=query,
        top_k=top_k,
    )
    
    return KnowledgeSearchResponse(
        results=[r.dict() for r in results],
        metadata={"total": len(results)},
    )


@router.get(
    "/assets",
    response_model=list[KnowledgeAsset],
    summary="List knowledge assets",
)
async def list_assets(
    skip: int = 0,
    limit: int = 100,
    repo: KnowledgeAssetRepository = Depends(get_knowledge_asset_repository),
    current_user = Depends(get_current_user),
) -> list[KnowledgeAsset]:
    """List knowledge assets."""
    return await repo.list(
        organization_id=current_user.organization_id, skip=skip, limit=limit
    )


@router.get(
    "/assets/{asset_id}",
    response_model=KnowledgeAsset,
    summary="Get a knowledge asset",
)
async def get_asset(
    asset_id: UUID,
    repo: KnowledgeAssetRepository = Depends(get_knowledge_asset_repository),
) -> KnowledgeAsset:
    """Get knowledge asset by ID."""
    asset = await repo.get_by_id(asset_id)
    if not asset:
        raise EntityNotFound("KnowledgeAsset", str(asset_id))
    return asset
