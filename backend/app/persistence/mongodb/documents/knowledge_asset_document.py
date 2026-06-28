"""KnowledgeAsset MongoDB document schema.

KnowledgeAssets are organization-level resources. ``workspace_id`` does NOT
appear here — the workspace-to-asset relationship is expressed by
``WorkspaceDocument.selected_knowledge_asset_ids`` (Option B).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from typing_extensions import TypedDict


class KnowledgeAssetDocument(TypedDict):
    """Raw BSON document stored in the ``knowledge_assets`` collection."""

    _id: str                        # UUID v4 as string
    organization_id: str            # Primary tenant isolation key
    schema_id: str
    name: str
    content_type: str               # AssetContentType enum value
    status: str                     # AssetStatus enum value
    raw_content: str | None
    structured_data: dict[str, Any]
    file_path: str | None
    qdrant_point_ids: list[str]
    processing_error: str | None
    uploaded_by: str                # User UUID as string
    lifecycle_state: str | None
    user_description: str | None
    processing_metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
