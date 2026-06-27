"""Organization MongoDB document schema."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from typing_extensions import TypedDict


class OrganizationDocument(TypedDict):
    """Raw BSON document stored in the ``organizations`` collection.

    Fields mirror the ``Organization`` domain model. ``_id`` stores the
    UUID string — Motor will serialise this as a BSON string, not ObjectId.
    """

    _id: str                          # UUID v4 as string
    name: str
    slug: str
    contact_email: str
    is_active: bool
    metadata: dict[str, str]
    created_at: datetime
    updated_at: datetime
