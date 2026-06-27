"""User MongoDB document schema."""

from __future__ import annotations

from datetime import datetime

from typing_extensions import TypedDict


class UserDocument(TypedDict):
    """Raw BSON document stored in the ``users`` collection."""

    _id: str           # UUID v4 as string
    organization_id: str
    email: str
    full_name: str
    role: str          # UserRole enum value
    status: str        # UserStatus enum value
    last_login_at: str | None   # ISO-8601 string or None
    created_at: datetime
    updated_at: datetime
