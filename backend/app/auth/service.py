"""Authentication and Authorization Service."""

from typing import Any
from datetime import datetime, timezone
from uuid import UUID

import structlog

from app.auth.exceptions import AuthError
from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.auth.models import AuditEvent, User
from app.auth.password import hash_password, verify_password
from app.auth.schemas import ChangePasswordRequest, LoginRequest, RegisterRequest, Token
from app.persistence.mongodb.repositories.audit_repository import AuditRepository
from app.persistence.mongodb.repositories.user_repository import UserRepository

logger = structlog.get_logger(__name__)


class AuthService:
    """Service handling authentication logic and audit logging."""

    def __init__(self, user_repo: UserRepository, audit_repo: AuditRepository) -> None:
        self.user_repo = user_repo
        self.audit_repo = audit_repo

    async def _log_audit(
        self, action: str, result: str, user_id: str | None = None, req_id: str = ""
    ) -> None:
        """Log an audit event both to MongoDB and via structlog."""
        event = AuditEvent(
            request_id=req_id,
            user_id=user_id,
            action=action,
            result=result,
        )
        await self.audit_repo.log_event(event)
        
        logger.info(
            "audit_event",
            action=action,
            result=result,
            user_id=user_id,
            request_id=req_id,
        )

    async def register(self, request: RegisterRequest, req_id: str = "") -> User:
        """Register a new user."""
        existing_user = await self.user_repo.get_by_email(request.email)
        if existing_user:
            await self._log_audit("register", "failed - email exists", req_id=req_id)
            raise AuthError("Email already registered")

        user = User(
            email=request.email,
            hashed_password=hash_password(request.password),
            full_name=request.full_name,
        )
        await self.user_repo.create(user)
        await self._log_audit("register", "success", str(user.id), req_id=req_id)
        return user

    def _create_token_payload(self, user: User) -> dict[str, Any]:
        """Create the payload for a JWT token."""
        roles = [mem.role.value for mem in user.memberships]
        org_ids = [str(oid) for oid in user.organization_ids]
        return {
            "sub": str(user.id),
            "email": user.email,
            "organization_ids": org_ids,
            "roles": roles,
        }

    async def login(self, request: LoginRequest, req_id: str = "") -> Token:
        """Authenticate user and return JWT tokens."""
        user = await self.user_repo.get_by_email(request.email)
        if not user or not verify_password(request.password, user.hashed_password):
            await self._log_audit("login", "failed - invalid credentials", req_id=req_id)
            raise AuthError("Invalid email or password")

        payload = self._create_token_payload(user)
        access_token = create_access_token(payload)
        refresh_token = create_refresh_token(payload)

        await self._log_audit("login", "success", str(user.id), req_id=req_id)

        return Token(access_token=access_token, refresh_token=refresh_token)

    async def refresh(self, refresh_token: str, req_id: str = "") -> Token:
        """Issue new tokens using a valid refresh token."""
        payload = decode_token(refresh_token)
        if not payload or "sub" not in payload:
            await self._log_audit("refresh", "failed - invalid token", req_id=req_id)
            raise AuthError("Invalid refresh token")

        user_id = payload["sub"]
        user = await self.user_repo.get_by_id(UUID(user_id))
        if not user:
            await self._log_audit("refresh", "failed - user not found", user_id, req_id=req_id)
            raise AuthError("Invalid user")

        payload_data = self._create_token_payload(user)
        access_token = create_access_token(payload_data)
        new_refresh_token = create_refresh_token(payload_data)

        await self._log_audit("refresh", "success", str(user.id), req_id=req_id)

        return Token(access_token=access_token, refresh_token=new_refresh_token)

    async def change_password(
        self, user_id: UUID, request: ChangePasswordRequest, req_id: str = ""
    ) -> None:
        """Change a user's password."""
        user = await self.user_repo.get_by_id(user_id)
        if not user or not verify_password(request.old_password, user.hashed_password):
            await self._log_audit("change_password", "failed - invalid old password", str(user_id), req_id=req_id)
            raise AuthError("Invalid old password")

        user.hashed_password = hash_password(request.new_password)
        user.updated_at = datetime.now(timezone.utc)
        await self.user_repo.update(user)

        await self._log_audit("change_password", "success", str(user_id), req_id=req_id)

    async def get_current_user(self, token: str) -> User:
        """Decode token and retrieve the user."""
        payload = decode_token(token)
        if not payload or "sub" not in payload:
            raise AuthError("Invalid token")

        user = await self.user_repo.get_by_id(UUID(payload["sub"]))
        if not user:
            raise AuthError("User not found")

        return user
