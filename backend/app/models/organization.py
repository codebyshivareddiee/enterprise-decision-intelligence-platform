"""Organization domain model.

An Organization is the top-level tenant boundary. All data within the
platform is owned by and siloed to exactly one Organization.  No data
ever crosses organization boundaries (see DO_NOT_CHANGE.md).
"""

from pydantic import EmailStr, Field

from app.models.base import AuditedModel


class Organization(AuditedModel):
    """Represents a tenant of the platform.

    Every other entity (users, workspaces, knowledge assets, etc.) is
    owned by an Organization and must include ``organization_id`` to
    enforce tenant isolation at query time.

    Attributes:
        name: Human-readable display name for the organization.
        slug: URL-safe, lowercase, unique identifier (e.g. ``acme-corp``).
            Used in API paths and logging.
        contact_email: Primary point of contact for the organization.
        is_active: Whether the organization is currently active on the
            platform. Inactive organizations cannot perform operations.
        metadata: Arbitrary key-value configuration bag for
            organization-level settings (billing tier, feature flags,
            etc.).  Never used to drive business logic — use typed
            fields for that.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable display name of the organization.",
    )
    slug: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="Unique, URL-safe slug (lowercase, hyphens only).",
    )
    contact_email: EmailStr = Field(
        ...,
        description="Primary contact email address for the organization.",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the organization is currently active.",
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Arbitrary organization-level configuration metadata.",
    )
