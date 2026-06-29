"""Knowledge Layer endpoints."""

import os
import tempfile

import structlog
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile

logger = structlog.get_logger(__name__)

from app.api.dependencies import (
    get_audit_repository,
    get_knowledge_asset_repository,
    get_knowledge_manager,
)
from app.api.v1.models.response import StandardResponse
from app.api.v1.models.responses import (
    KnowledgeSearchResponse,
    KnowledgeUploadResponse,
    KnowledgeAnalyzeResponse,
)
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
    "/analyze",
    response_model=StandardResponse[KnowledgeAnalyzeResponse],
    summary="Analyze a knowledge document without indexing",
    description="Uploads a file and performs AI analysis to suggest ingestion parameters.",
)
async def analyze_knowledge(
    request: Request,
    workspace_id: UUID | None = Form(None),
    organization_id: UUID = Form(...),
    description: str = Form(...),
    schema_id: UUID | None = Form(None),
    file: UploadFile = File(...),
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager),
) -> StandardResponse[KnowledgeAnalyzeResponse]:
    """Analyze a knowledge asset to suggest ingestion parameters."""
    content_bytes = await file.read()

    # ── Route binary vs text formats ──────────────────────────
    file_path: str | None = None
    raw_content: str | None = None

    if file.filename and file.filename.endswith(".pdf"):
        content_type = AssetContentType.PDF
        # Write raw PDF bytes to a temp file — PdfParser will extract text
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.write(content_bytes)
        tmp.close()
        file_path = tmp.name
    elif file.filename and file.filename.endswith(".md"):
        content_type = AssetContentType.MARKDOWN
        raw_content = content_bytes.decode("utf-8", errors="ignore")
    else:
        content_type = AssetContentType.TEXT
        raw_content = content_bytes.decode("utf-8", errors="ignore")

    import uuid
    dummy_schema_id = schema_id or uuid.uuid4()

    # In a real app we'd get the user from request context or current_user
    user_id_str = getattr(request.state, "user_id", str(uuid.uuid4()))
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        user_id = uuid.uuid4()

    # Create a temporary asset in memory (not saved to repo)
    temp_asset = KnowledgeAsset(
        organization_id=organization_id,
        schema_id=dummy_schema_id,
        name=file.filename or "uploaded_document",
        content_type=content_type,
        status=AssetStatus.PENDING,
        raw_content=raw_content,
        file_path=file_path,
        user_description=description,
        uploaded_by=user_id,
    )

    # Static for Hackathon: Provide available schemas so AI can make recommendations
    from app.models.knowledge_schema import KnowledgeSchema, SchemaField
    from app.models.enums import FieldType

    available_schemas = [
        KnowledgeSchema(
            id=uuid.UUID("d69a23d0-3e2b-47e2-8828-87b6be6f25db"),
            organization_id=organization_id,
            name="Candidate Profile",
            description="Profile schema for AI Engineer candidates",
            fields=[SchemaField(name="name", label="Name", field_type=FieldType.STRING, required=True)],
        ),
        KnowledgeSchema(
            id=uuid.UUID("e3f898a3-2f2c-499b-9a4c-1f55b99f30ce"),
            organization_id=organization_id,
            name="Software Vendor Profile",
            description="Evaluation profiles for third-party software vendors",
            fields=[SchemaField(name="vendor_name", label="Vendor Name", field_type=FieldType.STRING, required=True)],
        )
    ]

    # Perform analysis
    try:
        analysis_result, selection_method = await knowledge_manager.analyze_asset(
            temp_asset, available_schemas=available_schemas
        )
    finally:
        # Clean up temp file
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)

    logger.info(
        "ai_analysis_suggestions",
        suggested_schema_id=str(analysis_result.matched_schema_id) if analysis_result.matched_schema_id else None,
        suggested_chunking_strategy=analysis_result.chunking_strategy,
        suggested_chunk_profile=analysis_result.chunk_profile.value,
        suggested_lifecycle=analysis_result.suggested_lifecycle,
        suggested_metadata=analysis_result.suggested_metadata,
        confidence=analysis_result.confidence,
    )

    analyze_response = KnowledgeAnalyzeResponse(
        schema_selected=analysis_result.matched_schema_id,
        schema_name=None, # Will be handled by frontend for now
        chunking_strategy=analysis_result.chunking_strategy,
        chunk_profile=analysis_result.chunk_profile.value,
        confidence=analysis_result.confidence,
        processing_reasoning=analysis_result.reasoning,
        selection_method=selection_method,
        suggested_lifecycle=analysis_result.suggested_lifecycle,
        suggested_metadata=analysis_result.suggested_metadata,
    )

    return StandardResponse(
        success=True,
        data=analyze_response,
        message="Knowledge asset analyzed successfully.",
        request_id=getattr(request.state, "request_id", ""),
    )


@router.post(
    "/upload",
    response_model=StandardResponse[KnowledgeUploadResponse],
    summary="Upload a new knowledge document",
    description="Uploads a file, processes it, and indexes it into the vector store.",
)
async def upload_knowledge(
    request: Request,
    workspace_id: UUID | None = Form(None),
    organization_id: UUID = Form(...),
    description: str = Form(...),
    chunking_strategy_override: str | None = Form(None),
    chunk_profile_override: str | None = Form(None),
    schema_id_override: UUID | None = Form(None),
    file: UploadFile = File(...),
    repo: KnowledgeAssetRepository = Depends(get_knowledge_asset_repository),
    knowledge_manager: KnowledgeManager = Depends(get_knowledge_manager),
    audit_repo=Depends(get_audit_repository),
) -> StandardResponse[KnowledgeUploadResponse]:
    """Upload and index a knowledge asset."""
    content_bytes = await file.read()

    # ── Route binary vs text formats ──────────────────────────
    file_path: str | None = None
    raw_content: str | None = None

    if file.filename and file.filename.endswith(".pdf"):
        content_type = AssetContentType.PDF
        # Write raw PDF bytes to a temp file — PdfParser will extract text
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.write(content_bytes)
        tmp.close()
        file_path = tmp.name
    elif file.filename and file.filename.endswith(".md"):
        content_type = AssetContentType.MARKDOWN
        raw_content = content_bytes.decode("utf-8", errors="ignore")
    else:
        content_type = AssetContentType.TEXT
        raw_content = content_bytes.decode("utf-8", errors="ignore")

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
        raw_content=raw_content,
        file_path=file_path,
        user_description=description,
        uploaded_by=user_id,
    )

    asset = await repo.create(asset)

    if schema_id_override:
        asset.schema_id = schema_id_override

    # Temporary override mechanism - since KnowledgeManager.index_asset
    # invokes DocumentProcessor.process which runs the AI analyzer,
    # we simulate the overrides by injecting them into the available_schemas
    # or by forcing the AI analyzer to skip. But for simplicity, we let
    # DocumentProcessor process it. To prevent re-running AI analysis, we can
    # pass a mock schema or update the asset processing_metadata right after parsing,
    # but DocumentProcessor will rewrite it.
    # We will modify DocumentProcessor.process to respect overrides in the future,
    # but for now we can just let it run or hack the asset object before calling.

    try:
        point_ids = await knowledge_manager.index_asset(asset, available_schemas=[])
    finally:
        # Clean up temp file after processing
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)

    # Apply overrides after processing but before updating repo
    if asset.processing_metadata:
        if chunking_strategy_override:
            asset.processing_metadata.chunking_strategy = chunking_strategy_override
        if chunk_profile_override:
            asset.processing_metadata.chunk_profile = chunk_profile_override

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
        processing_reasoning=(meta.reasoning or "") if meta else "",
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
        assets = []

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
