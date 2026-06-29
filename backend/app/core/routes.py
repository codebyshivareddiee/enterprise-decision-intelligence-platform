"""Core platform routes — health check and readiness probe."""

from fastapi import APIRouter, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["platform"])


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    version: str
    details: dict | None = None


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check() -> HealthResponse:
    """Return service liveness status."""
    return HealthResponse(status="ok", version="0.1.0")


@router.get("/live", response_model=HealthResponse, summary="Liveness probe")
async def liveness_probe() -> HealthResponse:
    """Return service liveness status (mirrors health)."""
    return HealthResponse(status="ok", version="0.1.0")


@router.get("/ready", response_model=HealthResponse, summary="Readiness probe")
async def readiness_probe(request: Request) -> HealthResponse:
    """Return service readiness status by checking dependencies."""
    container = request.app.state.container

    # Check MongoDB
    mongo_status = "ok"
    try:
        await container.db.command("ping")
    except Exception:
        mongo_status = "error"

    # Check Qdrant
    qdrant_status = "ok"
    try:
        await container.qdrant_client.get_collections()
    except Exception:
        qdrant_status = "error"

    # Check AI Provider
    ai_status = "ok"
    try:
        health = await container.ai_manager.health_check()
        if health.get("status") != "ok":
            ai_status = "error"
    except Exception:
        ai_status = "error"

    overall_status = (
        "ready"
        if all(s == "ok" for s in (mongo_status, qdrant_status, ai_status))
        else "error"
    )

    return HealthResponse(
        status=overall_status,
        version="0.1.0",
        details={
            "mongodb": mongo_status,
            "qdrant": qdrant_status,
            "ai_provider": ai_status,
        },
    )


@router.get("/metrics", summary="Prometheus Metrics")
async def metrics() -> Response:
    """Expose Prometheus metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
