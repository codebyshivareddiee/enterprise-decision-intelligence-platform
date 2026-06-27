"""Core platform routes — health check and readiness probe."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["platform"])


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    version: str


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check() -> HealthResponse:
    """Return service liveness status.

    Used by Docker health checks and load balancers to confirm the service
    is running and able to accept requests.
    """
    return HealthResponse(status="ok", version="0.1.0")


@router.get("/ready", response_model=HealthResponse, summary="Readiness probe")
async def readiness_probe() -> HealthResponse:
    """Return service readiness status.

    In future tickets this will verify downstream connectivity (MongoDB,
    Qdrant). For P1 it mirrors the health check.
    """
    return HealthResponse(status="ready", version="0.1.0")
