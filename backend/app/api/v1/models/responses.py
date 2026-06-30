"""API Response Models."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    api_version: str
    build_version: str
    environment: str = "unknown"
    uptime_seconds: int = 0
    dependencies: dict[str, Any]


class KnowledgeUploadResponse(BaseModel):
    """Response after successfully uploading a knowledge asset."""

    asset_id: UUID
    schema_selected: UUID | None
    chunking_strategy: str
    chunk_profile: str
    processing_reasoning: str
    chunks_created: int


class KnowledgeAnalyzeResponse(BaseModel):
    """Response returning AI analysis recommendations without indexing."""

    schema_selected: UUID | None
    schema_name: str | None
    chunking_strategy: str
    chunk_profile: str
    confidence: float
    processing_reasoning: str
    selection_method: str
    suggested_lifecycle: list[str]
    suggested_metadata: list[str]


class KnowledgeSearchResponse(BaseModel):
    """Response containing search results."""

    results: list[dict[str, Any]]
    metadata: dict[str, Any]


class EvidenceItem(BaseModel):
    """Safe DTO representing a retrieved chunk of evidence."""

    asset_id: str
    asset_name: str | None = None
    chunk_id: str | None = None
    chunk_preview: str
    relevance_score: float | None = None
    metadata: dict[str, Any] | None = None


class WorkflowExecuteResponse(BaseModel):
    """Response after executing a decision workflow."""

    decision_id: UUID
    execution_plan: dict[str, Any] | None
    graph: dict[str, Any] | None = None
    execution_status: str
    requires_human_review: bool
    recommendation: dict[str, Any] | None
    explanation: str | None
    execution_trace: list[dict[str, Any]]
    supporting_evidence: list[EvidenceItem] | None = None


class WorkflowStatusResponse(BaseModel):
    """Response detailing the current status of a workflow."""

    decision_id: UUID
    status: str
    current_state: dict[str, Any]
    completed_nodes: list[str]
    failed_nodes: list[str]
    current_node: str | None
    execution_trace: list[dict[str, Any]]


class WorkspaceResponse(BaseModel):
    """Response payload representing a Workspace."""
    
    id: UUID
    created_at: Any
    updated_at: Any
    organization_id: UUID
    name: str
    description: str | None
    status: str
    knowledge_schema_id: UUID | None
    owner_id: UUID
    selected_knowledge_asset_ids: list[UUID]
    qdrant_collection_name: str | None
    goal: str | None
    success_metrics: str | None
    decision_points: str | None
    workspace_summary: dict[str, object] | None


class BusinessRuleResponse(BaseModel):
    """Response payload representing a BusinessRule."""

    id: UUID
    created_at: Any
    updated_at: Any
    organization_id: UUID
    workspace_id: UUID
    name: str
    description: str | None
    rule_type: str
    conditions: list[dict[str, Any]]
    is_active: bool
    weight: float
    priority: int
