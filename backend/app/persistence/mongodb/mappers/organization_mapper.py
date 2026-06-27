"""Organization mapper — Domain ↔ Mongo document."""

from __future__ import annotations

from uuid import UUID

from app.models.organization import Organization
from app.persistence.mongodb.documents.organization_document import OrganizationDocument


def to_document(org: Organization) -> OrganizationDocument:
    """Convert an ``Organization`` domain model to a Mongo document.

    Args:
        org: The domain model to persist.

    Returns:
        A dict-compatible ``OrganizationDocument`` ready for Motor insert/replace.
    """
    return OrganizationDocument(
        _id=str(org.id),
        name=org.name,
        slug=org.slug,
        contact_email=org.contact_email,
        is_active=org.is_active,
        metadata=org.metadata,
        created_at=org.created_at,
        updated_at=org.updated_at,
    )


def to_domain(doc: OrganizationDocument) -> Organization:
    """Convert a raw Mongo document to an ``Organization`` domain model.

    Args:
        doc: The raw BSON document retrieved from Motor.

    Returns:
        A validated ``Organization`` instance.
    """
    return Organization(
        id=UUID(doc["_id"]),
        name=doc["name"],
        slug=doc["slug"],
        contact_email=doc["contact_email"],
        is_active=doc["is_active"],
        metadata=doc["metadata"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )
