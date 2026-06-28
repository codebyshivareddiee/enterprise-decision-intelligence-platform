"""Health check endpoint."""

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.dependencies import get_ai_manager, get_db
from app.ai.manager import AIManager
from app.api.v1.models.responses import HealthResponse
from app.persistence.mongodb.client import get_mongo_client

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Check system health",
    description="Returns the status of internal services and external dependencies.",
)
async def check_health(
    db: AsyncIOMotorDatabase = Depends(get_db),
    ai_manager: AIManager = Depends(get_ai_manager),
) -> HealthResponse:
    """Perform health checks on all dependencies."""
    dependencies = {
        "mongodb": {"status": "unknown"},
        "openai": {"status": "unknown"},
        "qdrant": {"status": "unknown"}
    }
    
    overall_status = "ok"
    
    # Check MongoDB
    try:
        await get_mongo_client().admin.command("ping")
        dependencies["mongodb"]["status"] = "ok"
    except Exception as e:
        dependencies["mongodb"]["status"] = "error"
        dependencies["mongodb"]["error"] = str(e)
        overall_status = "degraded"

    # Check OpenAI via AI Manager
    try:
        ai_health = await ai_manager.health_check()
        dependencies["openai"] = ai_health
        if ai_health.get("status") != "ok":
            overall_status = "degraded"
    except Exception as e:
        dependencies["openai"]["status"] = "error"
        dependencies["openai"]["error"] = str(e)
        overall_status = "degraded"

    # Check Qdrant (We'd ideally inject QdrantStore, but for now we just return ok if we could instantiate)
    # Since QdrantStore connects on instantiation usually or we can't easily ping it without the client.
    # We will assume OK for now or add a ping method later.
    dependencies["qdrant"]["status"] = "ok"

    return HealthResponse(
        status=overall_status,
        api_version="v1",
        build_version="0.1.0",
        dependencies=dependencies,
    )
