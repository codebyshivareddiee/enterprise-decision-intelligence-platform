"""Global exception handlers for the API layer."""

import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.agents.base.exceptions import MissingArtifactError as AgentMissingArtifactError
from app.agents.planner.exceptions import PlannerError
from app.ai.exceptions import ProviderError
from app.core.exceptions import (
    DuplicateEntity,
    EntityNotFound,
    RepositoryError,
    ValidationError,
)
from app.workflow.exceptions import MissingArtifactError as WorkflowMissingArtifactError
from app.workflow.exceptions import WorkflowExecutionError
from app.auth.exceptions import AuthError, ForbiddenError
from app.api.v1.models.response import StandardErrorResponse


def build_error_response(request: Request, message: str, error_code: str) -> dict:
    req_id = getattr(request.state, "request_id", "")
    return StandardErrorResponse(
        success=False,
        message=message,
        error_code=error_code,
        request_id=req_id,
        timestamp=datetime.datetime.utcnow().isoformat(),
    ).model_dump()


def register_exception_handlers(app: FastAPI) -> None:
    """Register domain exceptions to HTTP response mappings."""
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=build_error_response(request, exc.detail, "HTTP_ERROR"),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=build_error_response(request, str(exc), "VALIDATION_ERROR"),
        )

    @app.exception_handler(AuthError)
    async def auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content=build_error_response(request, str(exc), "UNAUTHORIZED"),
        )

    @app.exception_handler(ForbiddenError)
    async def forbidden_error_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content=build_error_response(request, str(exc), "FORBIDDEN"),
        )

    @app.exception_handler(ProviderError)
    async def provider_error_handler(request: Request, exc: ProviderError) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content=build_error_response(request, str(exc), "AI_PROVIDER_ERROR"),
        )

    @app.exception_handler(PlannerError)
    async def planner_error_handler(request: Request, exc: PlannerError) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=build_error_response(request, str(exc), "PLANNER_ERROR"),
        )

    @app.exception_handler(WorkflowExecutionError)
    async def workflow_error_handler(request: Request, exc: WorkflowExecutionError) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=build_error_response(request, str(exc), "WORKFLOW_ERROR"),
        )

    @app.exception_handler(AgentMissingArtifactError)
    async def agent_missing_artifact_handler(request: Request, exc: AgentMissingArtifactError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=build_error_response(request, str(exc), "MISSING_ARTIFACT"),
        )

    @app.exception_handler(WorkflowMissingArtifactError)
    async def workflow_missing_artifact_handler(request: Request, exc: WorkflowMissingArtifactError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=build_error_response(request, str(exc), "MISSING_ARTIFACT"),
        )

    @app.exception_handler(EntityNotFound)
    async def entity_not_found_handler(request: Request, exc: EntityNotFound) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content=build_error_response(request, str(exc), "NOT_FOUND"),
        )

    @app.exception_handler(ValidationError)
    async def domain_validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=build_error_response(request, str(exc), "DOMAIN_VALIDATION_ERROR"),
        )

    @app.exception_handler(DuplicateEntity)
    async def duplicate_entity_handler(request: Request, exc: DuplicateEntity) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content=build_error_response(request, str(exc), "DUPLICATE_ENTITY"),
        )

    @app.exception_handler(RepositoryError)
    async def repository_error_handler(request: Request, exc: RepositoryError) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=build_error_response(request, str(exc), "REPOSITORY_ERROR"),
        )
