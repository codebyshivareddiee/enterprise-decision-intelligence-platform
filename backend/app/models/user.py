"""User domain model.

Users are authenticated individuals who belong to exactly one
Organization. Roles and permissions are scoped per user.
"""

from uuid import UUID

from pydantic import EmailStr, Field

from app.models.base import AuditedModel
from app.models.enums import UserRole, UserStatus


class User(AuditedModel):
    """Represents an authenticated platform user.

    A User belongs to exactly one Organization. Their role determines
    what actions they may perform within that organization and its
    workspaces.

    Attributes:
        organization_id: Foreign key to the owning Organization. All
            queries for users must be scoped by this field.
        email: Unique email address used for authentication and
            notifications.
        full_name: Display name shown in the UI.
        role: The user's role within the organization, which governs
            their permissions.
        status: Lifecycle status of the user account.
        last_login_at: UTC timestamp of the user's most recent
            successful login. ``None`` if the user has never logged in
            (e.g. invited but not yet accepted).
    """

    organization_id: UUID = Field(
        ...,
        description="ID of the Organization this user belongs to.",
    )
    email: EmailStr = Field(
        ...,
        description="Unique email address used for authentication.",
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="Display name of the user.",
    )
    role: UserRole = Field(
        default=UserRole.ANALYST,
        description="Role governing the user's permissions within the organization.",
    )
    status: UserStatus = Field(
        default=UserStatus.INVITED,
        description="Lifecycle status of the user account.",
    )
    last_login_at: None | str = Field(  # stored as ISO-8601 string to stay DB-agnostic
        default=None,
        description="UTC ISO-8601 timestamp of the user's most recent login, or None.",
    )
