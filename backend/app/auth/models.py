from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field


def now_utc() -> datetime:
    """Return the current time in UTC."""
    return datetime.now(timezone.utc)


class Role(str, Enum):
    """RBAC Roles."""
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    ORGANIZATION_ADMIN = "ORGANIZATION_ADMIN"
    WORKSPACE_ADMIN = "WORKSPACE_ADMIN"
    KNOWLEDGE_MANAGER = "KNOWLEDGE_MANAGER"
    DECISION_REVIEWER = "DECISION_REVIEWER"
    USER = "USER"


class Membership(BaseModel):
    """User access mapping."""
    organization_id: UUID
    workspace_ids: list[UUID] = Field(default_factory=list)
    role: Role


class User(BaseModel):
    """User domain model."""
    id: UUID = Field(default_factory=uuid4)
    email: EmailStr
    hashed_password: str
    full_name: str
    status: str = "active"
    organization_ids: list[UUID] = Field(default_factory=list)
    memberships: list[Membership] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

class AuditEvent(BaseModel):
    """Audit log entry."""
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=now_utc)
    request_id: str
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    workspace_id: Optional[str] = None
    action: str
    result: str
    ip_address: Optional[str] = None
    details: Optional[dict] = None
