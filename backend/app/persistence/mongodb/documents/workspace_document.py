"""Workspace MongoDB document schema."""

from __future__ import annotations

from datetime import datetime

from typing_extensions import TypedDict


class WorkspaceDocument(TypedDict):
    """Raw BSON document stored in the ``workspaces`` collection.

    ``selected_knowledge_asset_ids`` stores UUID strings for the org-level
    KnowledgeAssets this workspace has chosen to work with (Option B
    architecture). The assets themselves carry no ``workspace_id``.
    """

    _id: str  # UUID v4 as string
    organization_id: str
    name: str
    description: str | None
    status: str  # WorkspaceStatus enum value
    knowledge_schema_id: str | None
    owner_id: str
    selected_knowledge_asset_ids: list[str]  # UUID strings of selected assets
    qdrant_collection_name: str | None
    created_at: datetime
    updated_at: datetime
