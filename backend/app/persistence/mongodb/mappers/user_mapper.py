"""User mapper — Domain ↔ Mongo document."""

from __future__ import annotations

from uuid import UUID

from app.models.enums import UserRole, UserStatus
from app.models.user import User
from app.persistence.mongodb.documents.user_document import UserDocument


def to_document(user: User) -> UserDocument:
    """Convert a ``User`` domain model to a Mongo document."""
    return UserDocument(
        _id=str(user.id),
        organization_id=str(user.organization_id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        status=user.status.value,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def to_domain(doc: UserDocument) -> User:
    """Convert a raw Mongo document to a ``User`` domain model."""
    return User(
        id=UUID(doc["_id"]),
        organization_id=UUID(doc["organization_id"]),
        email=doc["email"],
        full_name=doc["full_name"],
        role=UserRole(doc["role"]),
        status=UserStatus(doc["status"]),
        last_login_at=doc["last_login_at"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )
