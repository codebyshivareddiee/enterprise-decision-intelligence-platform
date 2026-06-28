"""FastAPI dependencies for injecting services, repositories, and context."""

from typing import TypeVar

from fastapi import Depends, Request
from motor.motor_asyncio import AsyncIOMotorDatabase  # type: ignore

# Workflow Layer
from app.agents.planner.planner import Planner

# AI Layer
from app.ai.manager import AIManager

# Auth Layer
from app.auth.service import AuthService
from app.core.container import ServiceContainer

# Knowledge Layer
from app.knowledge.manager.knowledge_manager import KnowledgeManager
from app.persistence.mongodb.repositories.audit_repository import AuditRepository
from app.persistence.mongodb.repositories.business_rule_repository import (
    BusinessRuleRepository,
)
from app.persistence.mongodb.repositories.decision_history_repository import (
    DecisionHistoryRepository,
)
from app.persistence.mongodb.repositories.knowledge_asset_repository import (
    KnowledgeAssetRepository,
)

# Persistence Layer
from app.persistence.mongodb.repositories.organization_repository import (
    OrganizationRepository,
)
from app.persistence.mongodb.repositories.user_repository import UserRepository
from app.persistence.mongodb.repositories.workspace_repository import (
    WorkspaceRepository,
)

T = TypeVar("T")


def get_container(request: Request) -> ServiceContainer:
    """Return the global ServiceContainer from app state."""
    return request.app.state.container


def get_db(
    container: ServiceContainer = Depends(get_container),
) -> AsyncIOMotorDatabase:
    """Return the Motor database instance."""
    return container.db


def get_organization_repository(
    container: ServiceContainer = Depends(get_container),
) -> OrganizationRepository:
    """Return the OrganizationRepository."""
    return container.organization_repo


def get_workspace_repository(
    container: ServiceContainer = Depends(get_container),
) -> WorkspaceRepository:
    """Return the WorkspaceRepository."""
    return container.workspace_repo


def get_knowledge_asset_repository(
    container: ServiceContainer = Depends(get_container),
) -> KnowledgeAssetRepository:
    """Return the KnowledgeAssetRepository."""
    return container.knowledge_asset_repo


def get_decision_history_repository(
    container: ServiceContainer = Depends(get_container),
) -> DecisionHistoryRepository:
    """Return the DecisionHistoryRepository."""
    return container.decision_history_repo


def get_business_rule_repository(
    container: ServiceContainer = Depends(get_container),
) -> BusinessRuleRepository:
    """Return the BusinessRuleRepository."""
    return container.business_rule_repo


def get_audit_repository(
    container: ServiceContainer = Depends(get_container),
) -> AuditRepository:
    """Return the AuditRepository."""
    return container.audit_repo


def get_user_repository(
    container: ServiceContainer = Depends(get_container),
) -> UserRepository:
    """Return the UserRepository."""
    return container.user_repo


def get_ai_manager(container: ServiceContainer = Depends(get_container)) -> AIManager:
    """Return the AIManager."""
    return container.ai_manager


def get_knowledge_manager(
    container: ServiceContainer = Depends(get_container),
) -> KnowledgeManager:
    """Return the KnowledgeManager."""
    return container.knowledge_manager


def get_planner(
    container: ServiceContainer = Depends(get_container),
) -> Planner:
    """Return the Planner agent."""
    return container.planner


def get_auth_service(
    container: ServiceContainer = Depends(get_container),
) -> AuthService:
    """Return the AuthService."""
    return container.auth_service


def get_request_context(request: Request) -> dict[str, str]:
    """Extract context variables from the request for use in endpoints."""
    return {
        "request_id": request.headers.get("X-Request-ID", ""),
        "organization_id": request.headers.get("X-Organization-ID", ""),
        "workspace_id": request.headers.get("X-Workspace-ID", ""),
        "user_id": request.headers.get("X-User-ID", ""),
    }
