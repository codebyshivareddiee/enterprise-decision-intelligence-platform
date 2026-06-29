"""Health check endpoint."""

import time

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_container
from app.api.v1.models.response import StandardResponse
from app.api.v1.models.responses import HealthResponse
from app.core.container import ServiceContainer

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=StandardResponse[HealthResponse],
    summary="Check system health",
    description="Returns the status of internal services and external dependencies.",
)
async def check_health(
    request: Request,
    container: ServiceContainer = Depends(get_container),
) -> StandardResponse[HealthResponse]:
    """Perform health checks on all dependencies."""
    dependencies = {
        "mongodb": {"status": "unknown"},
        "openai": {"status": "unknown"},
        "qdrant": {"status": "unknown"},
    }

    overall_status = "READY"

    # Check MongoDB
    try:
        await container.mongo_client.admin.command("ping")
        dependencies["mongodb"]["status"] = "ok"
    except Exception as e:
        dependencies["mongodb"]["status"] = "error"
        dependencies["mongodb"]["error"] = str(e)
        overall_status = "DEGRADED"

    # Check OpenAI via AI Manager
    try:
        ai_health = await container.ai_manager.health_check()
        dependencies["openai"] = ai_health
        if ai_health.get("status") != "ok":
            overall_status = "DEGRADED"
    except Exception as e:
        dependencies["openai"]["status"] = "error"
        dependencies["openai"]["error"] = str(e)
        overall_status = "DEGRADED"

    # Check Qdrant
    try:
        # qdrant_client exposes get_collections which acts as a ping
        await container.qdrant_client.get_collections()
        dependencies["qdrant"]["status"] = "ok"
    except Exception as e:
        dependencies["qdrant"]["status"] = "error"
        dependencies["qdrant"]["error"] = str(e)
        overall_status = "DEGRADED"

    # If multiple dependencies fail, we might be UNHEALTHY
    failed = [k for k, v in dependencies.items() if v.get("status") == "error"]
    if len(failed) >= 2:
        overall_status = "UNHEALTHY"

    uptime_seconds = int(time.time() - container.start_time)

    health_data = HealthResponse(
        status=overall_status,
        api_version="v1",
        build_version="0.1.0",
        dependencies=dependencies,
        environment=container.settings.app_env,
        uptime_seconds=uptime_seconds,
    )

    return StandardResponse(
        success=True,
        data=health_data,
        message=f"System is {overall_status}",
        request_id=getattr(request.state, "request_id", ""),
    )
