from enum import Enum

from app.auth.models import Role


class Permission(str, Enum):
    """Fine-grained permissions."""

    MANAGE_ORGANIZATIONS = "MANAGE_ORGANIZATIONS"
    MANAGE_WORKSPACES = "MANAGE_WORKSPACES"
    MANAGE_USERS = "MANAGE_USERS"
    MANAGE_WORKSPACE = "MANAGE_WORKSPACE"
    UPLOAD_KNOWLEDGE = "UPLOAD_KNOWLEDGE"
    DELETE_KNOWLEDGE = "DELETE_KNOWLEDGE"
    SEARCH_KNOWLEDGE = "SEARCH_KNOWLEDGE"
    EXECUTE_WORKFLOWS = "EXECUTE_WORKFLOWS"
    RESUME_WORKFLOWS = "RESUME_WORKFLOWS"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    RECORD_OUTCOMES = "RECORD_OUTCOMES"
    EXECUTE_DECISIONS = "EXECUTE_DECISIONS"
    VIEW_OWN_DECISIONS = "VIEW_OWN_DECISIONS"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.PLATFORM_ADMIN: set(Permission),  # Has all permissions
    Role.ORGANIZATION_ADMIN: {
        Permission.MANAGE_ORGANIZATIONS,
        Permission.MANAGE_WORKSPACES,
        Permission.MANAGE_USERS,
    },
    Role.WORKSPACE_ADMIN: {
        Permission.MANAGE_WORKSPACE,
        Permission.UPLOAD_KNOWLEDGE,
        Permission.EXECUTE_WORKFLOWS,
    },
    Role.KNOWLEDGE_MANAGER: {
        Permission.UPLOAD_KNOWLEDGE,
        Permission.DELETE_KNOWLEDGE,
        Permission.SEARCH_KNOWLEDGE,
    },
    Role.DECISION_REVIEWER: {
        Permission.RESUME_WORKFLOWS,
        Permission.HUMAN_APPROVAL,
        Permission.RECORD_OUTCOMES,
    },
    Role.USER: {
        Permission.SEARCH_KNOWLEDGE,
        Permission.EXECUTE_DECISIONS,
        Permission.VIEW_OWN_DECISIONS,
    },
}


def has_permission(role: Role, permission: Permission) -> bool:
    """Check if a role grants a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())
