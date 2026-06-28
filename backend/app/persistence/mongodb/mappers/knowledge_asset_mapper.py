"""KnowledgeAsset mapper — Domain ↔ Mongo document."""

from __future__ import annotations

from uuid import UUID

from app.models.enums import AssetContentType, AssetStatus
from app.models.knowledge_asset import KnowledgeAsset, ProcessingMetadata
from app.persistence.mongodb.documents.knowledge_asset_document import (
    KnowledgeAssetDocument,
)


def to_document(asset: KnowledgeAsset) -> KnowledgeAssetDocument:
    """Convert a ``KnowledgeAsset`` domain model to a Mongo document.

    ``workspace_id`` is intentionally absent — assets are org-owned.
    The workspace-to-asset relationship lives in ``WorkspaceDocument``.
    """
    return KnowledgeAssetDocument(
        _id=str(asset.id),
        organization_id=str(asset.organization_id),
        schema_id=str(asset.schema_id),
        name=asset.name,
        content_type=asset.content_type.value,
        status=asset.status.value,
        raw_content=asset.raw_content,
        structured_data=dict(asset.structured_data),
        file_path=asset.file_path,
        qdrant_point_ids=list(asset.qdrant_point_ids),
        processing_error=asset.processing_error,
        uploaded_by=str(asset.uploaded_by),
        lifecycle_state=asset.lifecycle_state,
        user_description=asset.user_description,
        processing_metadata=asset.processing_metadata.model_dump() if asset.processing_metadata else None,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


def to_domain(doc: KnowledgeAssetDocument) -> KnowledgeAsset:
    """Convert a raw Mongo document to a ``KnowledgeAsset`` domain model."""
    return KnowledgeAsset(
        id=UUID(doc["_id"]),
        organization_id=UUID(doc["organization_id"]),
        schema_id=UUID(doc["schema_id"]),
        name=doc["name"],
        content_type=AssetContentType(doc["content_type"]),
        status=AssetStatus(doc["status"]),
        raw_content=doc["raw_content"],
        structured_data=doc["structured_data"],
        file_path=doc["file_path"],
        qdrant_point_ids=doc["qdrant_point_ids"],
        processing_error=doc["processing_error"],
        uploaded_by=UUID(doc["uploaded_by"]),
        lifecycle_state=doc.get("lifecycle_state"),
        user_description=doc.get("user_description"),
        processing_metadata=ProcessingMetadata(**doc["processing_metadata"]) if doc.get("processing_metadata") else None,
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )
