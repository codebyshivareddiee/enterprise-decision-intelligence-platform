"""AuditRepository — Appends audit events to the ``audit_events`` collection."""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.models import AuditEvent
from app.persistence.mongodb import collections as col


class AuditRepository:
    """Async repository for Audit events persistence."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[col.AUDIT_EVENTS]

    async def log_event(self, event: AuditEvent) -> AuditEvent:
        doc = event.model_dump(mode="json")
        doc["_id"] = doc.pop("id")
        await self._collection.insert_one(doc)
        return event

    async def list(self, skip: int = 0, limit: int = 100) -> list[AuditEvent]:
        cursor = self._collection.find({}).sort("timestamp", -1).skip(skip).limit(limit)
        results = []
        async for doc in cursor:
            doc["id"] = doc.pop("_id")
            results.append(AuditEvent.model_validate(doc))
        return results
