"""Workspace mapper — Domain ↔ Mongo document."""

from __future__ import annotations

from uuid import UUID

from app.models.enums import WorkspaceStatus
from app.models.workspace import Workspace
from app.persistence.mongodb.documents.workspace_document import WorkspaceDocument


def to_document(workspace: Workspace) -> WorkspaceDocument:
    """Convert a ``Workspace`` domain model to a Mongo document."""
    return WorkspaceDocument(
        _id=str(workspace.id),
        organization_id=str(workspace.organization_id),
        name=workspace.name,
        description=workspace.description,
        status=workspace.status.value,
        knowledge_schema_id=(
            str(workspace.knowledge_schema_id)
            if workspace.knowledge_schema_id is not None
            else None
        ),
        owner_id=str(workspace.owner_id),
        selected_knowledge_asset_ids=[
            str(aid) for aid in workspace.selected_knowledge_asset_ids
        ],
        qdrant_collection_name=workspace.qdrant_collection_name,
        goal=workspace.goal,
        success_metrics=workspace.success_metrics,
        decision_points=workspace.decision_points,
        workspace_summary=workspace.workspace_summary,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


def to_domain(doc: WorkspaceDocument) -> Workspace:
    """Convert a raw Mongo document to a ``Workspace`` domain model."""
    return Workspace(
        id=UUID(doc["_id"]),
        organization_id=UUID(doc["organization_id"]),
        name=doc["name"],
        description=doc["description"],
        status=WorkspaceStatus(doc["status"]),
        knowledge_schema_id=(
            UUID(doc["knowledge_schema_id"])
            if doc["knowledge_schema_id"] is not None
            else None
        ),
        owner_id=UUID(doc["owner_id"]),
        selected_knowledge_asset_ids=[
            UUID(aid) for aid in doc["selected_knowledge_asset_ids"]
        ],
        qdrant_collection_name=doc.get("qdrant_collection_name"),
        goal=doc.get("goal"),
        success_metrics=doc.get("success_metrics"),
        decision_points=doc.get("decision_points"),
        workspace_summary=doc.get("workspace_summary"),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )
