"""Authentication and Authorization FastAPI Dependencies."""

from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.exceptions import AuthError, ForbiddenError
from app.auth.models import Role, User
from app.auth.permissions import Permission, has_permission
from app.auth.service import AuthService
from app.persistence.mongodb.database import get_database
from app.persistence.mongodb.repositories.audit_repository import AuditRepository
from app.persistence.mongodb.repositories.user_repository import UserRepository

# We use the same get_db dependency as the rest of the application
def get_db() -> AsyncIOMotorDatabase:
    return get_database()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_user_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_audit_repository(db: AsyncIOMotorDatabase = Depends(get_db)) -> AuditRepository:
    return AuditRepository(db)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    audit_repo: AuditRepository = Depends(get_audit_repository),
) -> AuthService:
    return AuthService(user_repo, audit_repo)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    try:
        user = await auth_service.get_current_user(token)
        return user
    except AuthError as e:
        raise e


def require_permission(permission: Permission):
    """Dependency to enforce RBAC permissions, considering org/workspace scope."""

    async def dependency(
        request: Request,
        current_user: User = Depends(get_current_user),
    ) -> User:
        org_id_str = request.path_params.get("organization_id")
        workspace_id_str = request.path_params.get("workspace_id")

        # If Platform Admin, bypass all checks
        if any(m.role == Role.PLATFORM_ADMIN for m in current_user.memberships):
            return current_user

        applicable_role = None

        if workspace_id_str:
            try:
                workspace_id = UUID(workspace_id_str)
            except ValueError:
                raise ForbiddenError("Invalid workspace ID format")
                
            for mem in current_user.memberships:
                if workspace_id in mem.workspace_ids:
                    applicable_role = mem.role
                    break
            
            # If no workspace-specific access, fallback to see if they have org-level access
            if not applicable_role and org_id_str:
                try:
                    org_id = UUID(org_id_str)
                    for mem in current_user.memberships:
                        if mem.organization_id == org_id:
                            applicable_role = mem.role
                            break
                except ValueError:
                    pass

        elif org_id_str:
            try:
                org_id = UUID(org_id_str)
            except ValueError:
                raise ForbiddenError("Invalid organization ID format")
                
            for mem in current_user.memberships:
                if mem.organization_id == org_id:
                    applicable_role = mem.role
                    break

        if applicable_role:
            if not has_permission(applicable_role, permission):
                raise ForbiddenError(f"Requires permission {permission.value} for this scope")
            return current_user

        # If no specific scope is requested (e.g., global endpoint), check if any membership grants it
        if not org_id_str and not workspace_id_str:
            has_perm = any(has_permission(m.role, permission) for m in current_user.memberships)
            if not has_perm:
                raise ForbiddenError(f"Requires permission {permission.value}")
            return current_user
        
        raise ForbiddenError("You do not have access to this resource")

    return dependency
