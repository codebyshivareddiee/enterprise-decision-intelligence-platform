"""Global exception handlers for the API layer."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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


def register_exception_handlers(app: FastAPI) -> None:
    """Register domain exceptions to HTTP response mappings."""

    @app.exception_handler(ProviderError)
    async def provider_error_handler(
        request: Request,
        exc: ProviderError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={"detail": "AI Provider error.", "message": str(exc)},
        )

    @app.exception_handler(PlannerError)
    async def planner_error_handler(
        request: Request,
        exc: PlannerError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": "Planner execution failed.", "message": str(exc)},
        )

    @app.exception_handler(WorkflowExecutionError)
    async def workflow_error_handler(
        request: Request,
        exc: WorkflowExecutionError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": "Workflow execution failed.", "message": str(exc)},
        )

    @app.exception_handler(AgentMissingArtifactError)
    async def agent_missing_artifact_handler(
        request: Request,
        exc: AgentMissingArtifactError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": "Missing required artifact.", "message": str(exc)},
        )

    @app.exception_handler(WorkflowMissingArtifactError)
    async def workflow_missing_artifact_handler(
        request: Request,
        exc: WorkflowMissingArtifactError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": "Missing required artifact.", "message": str(exc)},
        )

    @app.exception_handler(EntityNotFound)
    async def entity_not_found_handler(
        request: Request,
        exc: EntityNotFound,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": "Resource not found.", "message": str(exc)},
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(
        request: Request,
        exc: ValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": "Validation error.", "message": str(exc)},
        )

    @app.exception_handler(DuplicateEntity)
    async def duplicate_entity_handler(
        request: Request,
        exc: DuplicateEntity,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": "Entity already exists.", "message": str(exc)},
        )

    @app.exception_handler(RepositoryError)
    async def repository_error_handler(
        request: Request,
        exc: RepositoryError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": "Repository operation failed.", "message": str(exc)},
        )
