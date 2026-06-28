"""KnowledgeAsset domain model.

A KnowledgeAsset is an organization-level resource. It is NOT owned by a
single workspace. Workspaces reference the assets they use via
``Workspace.selected_knowledge_asset_ids``. This makes assets reusable across
multiple workspaces within the same organization.

After upload, the asset is chunked and embedded (P3 workflow); the resulting
Qdrant point IDs are stored here as references back to the vector store.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.base import AuditedModel
from app.models.enums import AssetContentType, AssetStatus


class ProcessingMetadata(BaseModel):
    """Metadata detailing how the asset was processed by the ingestion pipeline."""
    chunking_strategy: str = Field(description="Name of the chunker used (e.g., HeadingChunker)")
    chunk_profile: str = Field(description="Chunk profile used (e.g., SMALL, MEDIUM)")
    chunk_size: int = Field(description="Selected chunk size in characters")
    chunk_overlap: int = Field(description="Selected chunk overlap in characters")
    selection_method: str = Field(description="Method used to decide chunking (rule_based, ai, manual)")
    reasoning: str | None = Field(default=None, description="Explanation of why this strategy was chosen")
    confidence: float = Field(description="Confidence score (0.0 to 1.0) of the selection method")
    processing_version: str = Field(description="Version of the processing pipeline")
    processed_at: datetime = Field(default_factory=datetime.utcnow, description="When the asset was processed")

class KnowledgeAsset(AuditedModel):
    """A single knowledge record or document owned by an Organization.

    Assets are organization-scoped, not workspace-scoped. A workspace
    selects which assets it works with via ``selected_knowledge_asset_ids``
    on the ``Workspace`` model. The same asset can therefore be referenced by
    multiple workspaces within the same organization without duplication.

    After processing, ``qdrant_point_ids`` contains references to the
    embedded chunks stored in Qdrant, enabling the Retriever to fetch
    full business context after a vector search (see DO_NOT_CHANGE.md).

    Attributes:
        organization_id: Owning organization — the primary tenant isolation
            key. All asset queries must be scoped by this field.
        schema_id: KnowledgeSchema this asset must conform to. The schema
            is also organization-scoped, so conformance stays within the
            tenant boundary.
        name: Human-readable asset name or document title.
        content_type: Format category of the uploaded content.
        status: Current processing/availability status.
        raw_content: The original text content (or JSON-serialised
            structured data). Stored here for reference; the processed
            chunks live in Qdrant.
        structured_data: Schema-conformant field values extracted from
            the asset. Keys match ``SchemaField.name`` values.
        file_path: Optional path or URL to the source file in object
            storage (e.g., S3/GCS). ``None`` for manually entered
            structured records.
        qdrant_point_ids: List of Qdrant point IDs created during the
            embedding workflow. Empty until the asset is fully processed.
        processing_error: Human-readable error message if ``status``
            is ``FAILED``. ``None`` otherwise.
        uploaded_by: User ID of the person who uploaded this asset.
    """

    organization_id: UUID = Field(
        ...,
        description="ID of the owning Organization.",
    )
    schema_id: UUID = Field(
        ...,
        description="ID of the KnowledgeSchema this asset conforms to.",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Human-readable asset name or document title.",
    )
    content_type: AssetContentType = Field(
        ...,
        description="Format category of the uploaded content.",
    )
    status: AssetStatus = Field(
        default=AssetStatus.PENDING,
        description="Current processing / availability status of the asset.",
    )
    raw_content: str | None = Field(
        default=None,
        description="Original text content or JSON-serialised structured data.",
    )
    structured_data: dict[str, object] = Field(
        default_factory=dict,
        description=(
            "Schema-conformant field values. Keys must match SchemaField.name "
            "values from the associated KnowledgeSchema."
        ),
    )
    file_path: str | None = Field(
        default=None,
        description="Object-storage path or URL to the source file, if applicable.",
    )
    qdrant_point_ids: list[str] = Field(
        default_factory=list,
        description="Qdrant point IDs for the embedded chunks of this asset.",
    )
    processing_error: str | None = Field(
        default=None,
        description="Error message if processing failed. None otherwise.",
    )
    uploaded_by: UUID = Field(
        ...,
        description="User ID of the person who uploaded this asset.",
    )
    lifecycle_state: str | None = Field(
        default=None,
        description="The current lifecycle state of this asset, derived from the schema's initial state upon ingestion.",
    )
    user_description: str | None = Field(
        default=None,
        max_length=2000,
        description="2-3 line description provided by the user at upload time.",
    )
    processing_metadata: ProcessingMetadata | None = Field(
        default=None,
        description="Details on how the Knowledge Layer decided to parse and chunk this document.",
    )

