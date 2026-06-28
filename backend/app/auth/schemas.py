from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.auth.models import Membership


class Token(BaseModel):
    """JWT response payload."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str
    full_name: str


class LoginRequest(BaseModel):
    """User login request. 
    (Note: Swagger UI typically uses OAuth2PasswordRequestForm instead, 
    but we keep this for JSON-based login if needed.)
    """
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Password change request."""
    old_password: str
    new_password: str


class UserResponse(BaseModel):
    """User response model (no password)."""
    id: UUID
    email: EmailStr
    full_name: str
    status: str
    organization_ids: list[UUID]
    memberships: list[Membership]
    created_at: datetime
    updated_at: datetime
