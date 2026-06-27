"""Workspace domain model.

A Workspace is a working environment within an Organization. It ties
together a KnowledgeSchema and a set of
BusinessRules into a coherent decision-making context.

KnowledgeAssets are organization-owned resources. A Workspace does not
own them; instead it maintains ``selected_knowledge_asset_ids`` — an
explicit list of asset IDs from the organization library that this
workspace has selected for use. The same asset can therefore be
referenced by multiple workspaces without duplication.

Multiple Workspaces can coexist within one Organization (e.g., one for
hiring engineers, another for vendor selection).
"""

from uuid import UUID

from pydantic import Field

from app.models.base import AuditedModel
from app.models.enums import WorkspaceStatus


class Workspace(AuditedModel):
    """A domain-specific decision-making environment within an Organization.

    All recommendation runs, business rules, lifecycle definitions (via schema), and
    preference profiles are scoped to a Workspace. Workspaces never share
    knowledge across Organization boundaries (see DO_NOT_CHANGE.md).

    KnowledgeAssets are organization-owned; this workspace holds only an
    explicit selection of asset IDs via ``selected_knowledge_asset_ids``.

    Attributes:
        organization_id: Owning organization — all queries must include
            this for tenant isolation.
        name: Human-readable workspace name (e.g. ``"Senior AI Engineer
            Hiring – Q3 2025"``).
        description: Optional longer description of the workspace purpose.
        status: Current operational status of the workspace.
        knowledge_schema_id: Reference to the KnowledgeSchema that
            defines the shape of assets selected into this workspace
            and the lifecycle stages. ``None`` until a schema is assigned.
        owner_id: User ID of the workspace owner / primary analyst.
        selected_knowledge_asset_ids: Ordered list of KnowledgeAsset IDs
            (from the organization library) that this workspace has
            selected for use. The service layer resolves these IDs into
            full asset objects when needed.
        qdrant_collection_name: The Qdrant collection that stores
            embeddings for this workspace's selected assets. Populated
            during the knowledge upload workflow (P3). ``None`` until
            the first asset is embedded.
    """

    organization_id: UUID = Field(
        ...,
        description="ID of the owning Organization.",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="Human-readable workspace name.",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional description of this workspace's purpose.",
    )
    status: WorkspaceStatus = Field(
        default=WorkspaceStatus.DRAFT,
        description="Operational status of the workspace.",
    )
    knowledge_schema_id: UUID | None = Field(
        default=None,
        description="ID of the KnowledgeSchema assigned to this workspace.",
    )
    owner_id: UUID = Field(
        ...,
        description="User ID of the workspace owner.",
    )
    selected_knowledge_asset_ids: list[UUID] = Field(
        default_factory=list,
        description=(
            "Ordered list of KnowledgeAsset IDs (from the organization library) "
            "selected for use in this workspace. Resolved by the service layer."
        ),
    )
    qdrant_collection_name: str | None = Field(
        default=None,
        description=(
            "Qdrant collection name storing embeddings for this workspace's "
            "selected assets. Populated by the knowledge upload workflow."
        ),
    )
