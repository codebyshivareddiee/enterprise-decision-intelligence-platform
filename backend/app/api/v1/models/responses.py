"""API Response Models."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.decision_history import DecisionHistory
from app.models.knowledge_asset import KnowledgeAsset


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


class KnowledgeSearchResponse(BaseModel):
    """Response containing search results."""

    results: list[dict[str, Any]]
    metadata: dict[str, Any]


class WorkflowExecuteResponse(BaseModel):
    """Response after executing a decision workflow."""

    decision_id: UUID
    execution_plan: dict[str, Any] | None
    execution_status: str
    requires_human_review: bool
    recommendation: dict[str, Any] | None
    explanation: str | None
    execution_trace: list[dict[str, Any]]


class WorkflowStatusResponse(BaseModel):
    """Response detailing the current status of a workflow."""

    decision_id: UUID
    status: str
    current_state: dict[str, Any]
    completed_nodes: list[str]
    failed_nodes: list[str]
    current_node: str | None
    execution_trace: list[dict[str, Any]]
