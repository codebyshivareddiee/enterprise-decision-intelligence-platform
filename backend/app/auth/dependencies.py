"""Authentication and Authorization FastAPI Dependencies."""

from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer

from app.api.dependencies import get_auth_service
from app.auth.exceptions import AuthError, ForbiddenError
from app.auth.models import Role, User
from app.auth.permissions import Permission, has_permission
from app.auth.service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    try:
        user = await auth_service.get_current_user(token)
        request.state.user_id = str(user.id)
        if user.organization_ids:
            request.state.organization_id = str(user.organization_ids[0])
        return user
    except AuthError as e:
        raise e


def require_authenticated_user():
    """Dependency that ensures a valid user is authenticated."""
    return get_current_user


def require_role(role: Role):
    """Dependency to enforce that the user has a specific role globally or in any scope."""

    async def dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if any(m.role == Role.PLATFORM_ADMIN for m in current_user.memberships):
            return current_user

        has_role = any(m.role == role for m in current_user.memberships)
        if not has_role:
            raise ForbiddenError(f"Requires role {role.value}")
        return current_user

    return dependency


def require_organization_access(permission: Permission):
    """Dependency to enforce RBAC permissions for a specific organization."""

    async def dependency(
        request: Request,
        current_user: User = Depends(get_current_user),
    ) -> User:
        if any(m.role == Role.PLATFORM_ADMIN for m in current_user.memberships):
            return current_user

        org_id_str = request.path_params.get("organization_id")
        if not org_id_str:
            raise ForbiddenError("Missing organization ID in request path")

        try:
            org_id = UUID(org_id_str)
        except ValueError:
            raise ForbiddenError("Invalid organization ID format")

        applicable_role = None
        for mem in current_user.memberships:
            if mem.organization_id == org_id:
                applicable_role = mem.role
                break

        if applicable_role and has_permission(applicable_role, permission):
            return current_user

        raise ForbiddenError("You do not have the required access to this organization")

    return dependency


def require_workspace_access(permission: Permission):
    """Dependency to enforce RBAC permissions for a specific workspace."""

    async def dependency(
        request: Request,
        current_user: User = Depends(get_current_user),
    ) -> User:
        if any(m.role == Role.PLATFORM_ADMIN for m in current_user.memberships):
            return current_user

        workspace_id_str = request.path_params.get("workspace_id")
        if not workspace_id_str:
            raise ForbiddenError("Missing workspace ID in request path")

        try:
            workspace_id = UUID(workspace_id_str)
        except ValueError:
            raise ForbiddenError("Invalid workspace ID format")

        applicable_role = None
        for mem in current_user.memberships:
            if workspace_id in mem.workspace_ids:
                applicable_role = mem.role
                break

        if not applicable_role:
            # Fallback to org level if they have access to the org this workspace belongs to
            org_id_str = request.path_params.get("organization_id")
            if not org_id_str:
                org_id_str = getattr(request.state, "organization_id", None)
                
            if org_id_str:
                try:
                    org_id = UUID(org_id_str)
                    for mem in current_user.memberships:
                        if mem.organization_id == org_id:
                            applicable_role = mem.role
                            break
                except ValueError:
                    pass

        if applicable_role and has_permission(applicable_role, permission):
            return current_user

        raise ForbiddenError("You do not have the required access to this workspace")

    return dependency
