"""User mapper — Domain ↔ Mongo document."""

from typing import Any
from uuid import UUID
from datetime import datetime
from app.auth.models import Membership, Role, User


def to_document(user: User) -> dict[str, Any]:
    """Convert a ``User`` domain model to a Mongo document."""
    doc = user.model_dump(mode="json")
    # MongoDB uses _id instead of id
    doc["_id"] = doc.pop("id")
    return doc


def to_domain(doc: dict[str, Any]) -> User:
    """Convert a raw Mongo document to a ``User`` domain model."""
    if "_id" in doc:
        doc["id"] = doc.pop("_id")
    
    # Parse dates if they are strings
    if isinstance(doc.get("created_at"), str):
        doc["created_at"] = datetime.fromisoformat(doc["created_at"].replace("Z", "+00:00"))
    if isinstance(doc.get("updated_at"), str):
        doc["updated_at"] = datetime.fromisoformat(doc["updated_at"].replace("Z", "+00:00"))
        
    return User.model_validate(doc)
