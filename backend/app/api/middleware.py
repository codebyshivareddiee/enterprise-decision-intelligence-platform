"""API middleware for request context, logging, and timing."""

import time
import uuid

import structlog
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = structlog.get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to capture request context and inject it into structlog."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process the request, bind context vars, and add tracking headers."""
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        # Extract from Headers initially (e.g. for request_id)
        organization_id = request.headers.get("X-Organization-ID", "unknown")
        workspace_id = request.headers.get("X-Workspace-ID", "unknown")
        user_id = request.headers.get("X-User-ID", "unknown")
        roles = "unknown"

        # If Authorization header exists, decode statelessly to enrich context
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            from app.auth.jwt import decode_token

            payload = decode_token(token)
            if payload:
                user_id = payload.get("sub", user_id)
                orgs = payload.get("organization_ids", [])
                if orgs:
                    organization_id = ",".join(orgs)
                role_list = payload.get("roles", [])
                if role_list:
                    roles = ",".join(role_list)

        # Bind to structlog context vars
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            user_id=user_id,
            roles=roles,
        )

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            # Re-raise so the global exception handlers or uvicorn can catch it
            raise
        finally:
            process_time = time.perf_counter() - start_time
            # Only log valid status codes if response was returned normally
            # If an exception was raised and not caught by an exception handler, response is not bound
            status_code = response.status_code if "response" in locals() else 500

            # Do not log sensitive endpoints or health checks aggressively if desired,
            # but for now we log all.
            logger.info(
                "request_completed",
                method=request.method,
                url=str(request.url.path),
                status_code=status_code,
                process_time_ms=round(process_time * 1000, 2),
            )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        return response


def register_middleware(app: FastAPI) -> None:
    """Register all custom middleware with the FastAPI application."""
    app.add_middleware(RequestContextMiddleware)
