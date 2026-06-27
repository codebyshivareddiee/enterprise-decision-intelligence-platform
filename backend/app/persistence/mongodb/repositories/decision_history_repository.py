"""DecisionHistoryRepository — append-only access for the ``decision_history`` collection.

Decision History is a permanent, append-only audit trail. Records are never
mutated or deleted (architectural invariant from DO_NOT_CHANGE.md).

This repository deliberately omits ``update()`` and ``delete()`` methods to
make the append-only constraint explicit at the code level.
"""

from __future__ import annotations

from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase  # type: ignore[import-untyped]

from app.models.decision_history import DecisionHistory
from app.persistence.mongodb import collections as col
from app.persistence.mongodb.mappers import decision_history_mapper


class DecisionHistoryRepository:
    """Async append-only repository for DecisionHistory persistence.

    ``update()`` and ``delete()`` are intentionally absent to enforce the
    append-only architectural invariant.  If the service layer needs to
    "correct" a decision, it must append a new correcting record.

    Args:
        db: Motor database handle injected at construction time.
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
        self._collection = db[col.DECISION_HISTORY]

    async def create(self, decision: DecisionHistory) -> DecisionHistory:
        """Append a new DecisionHistory record.

        Args:
            decision: Fully constructed ``DecisionHistory`` domain model.

        Returns:
            The stored ``DecisionHistory`` (identity after insert).
        """
        document = decision_history_mapper.to_document(decision)
        await self._collection.insert_one(document)
        return decision

    async def get_by_id(self, decision_id: UUID) -> DecisionHistory | None:
        """Retrieve a DecisionHistory record by its UUID.

        Args:
            decision_id: The UUID of the decision record to fetch.

        Returns:
            The ``DecisionHistory`` if found, ``None`` otherwise.
        """
        raw = await self._collection.find_one({"_id": str(decision_id)})
        if raw is None:
            return None
        return decision_history_mapper.to_domain(raw)

    async def list(
        self,
        *,
        workspace_id: UUID,
        skip: int = 0,
        limit: int = 200,
    ) -> list[DecisionHistory]:
        """Return decision history records scoped to a workspace, oldest first.

        Learner reads records in insertion order to process them sequentially.

        Args:
            workspace_id: Workspace filter.
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.

        Returns:
            List of ``DecisionHistory`` domain models ordered by ``created_at`` ascending.
        """
        cursor = (
            self._collection
            .find({"workspace_id": str(workspace_id)})
            .sort("created_at", 1)
            .skip(skip)
            .limit(limit)
        )
        return [decision_history_mapper.to_domain(doc) async for doc in cursor]
