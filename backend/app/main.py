"""Enterprise Decision Intelligence Platform — FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.core.logging import configure_logging

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    """Manage application startup and shutdown lifecycle."""
    settings = get_settings()
    configure_logging(settings.app_log_level)

    logger.info(
        "application.startup",
        env=settings.app_env,
        host=settings.app_host,
        port=settings.app_port,
    )

    yield

    logger.info("application.shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Enterprise Decision Intelligence Platform",
        description="Domain-agnostic AI-driven decision intelligence engine.",
        version="0.1.0",
        docs_url="/docs" if settings.app_debug else None,
        redoc_url="/redoc" if settings.app_debug else None,
        lifespan=lifespan,
    )

    # ── Middleware ──────────────────────────────────────────────────────────
    from app.api.middleware import register_middleware  # noqa: PLC0415
    register_middleware(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.app_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception Handlers ──────────────────────────────────────────────────
    from app.api.exception_handlers import register_exception_handlers  # noqa: PLC0415
    register_exception_handlers(app)

    # ── Routers ─────────────────────────────────────────────────────────────
    from app.core.routes import router as core_router  # noqa: PLC0415
    from app.api.router import api_router  # noqa: PLC0415

    app.include_router(core_router)
    app.include_router(api_router)

    return app


app = create_app()
