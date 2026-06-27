"""RecommendationRepository — CRUD access for the ``recommendations`` collection."""

from __future__ import annotations

from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase  # type: ignore[import-untyped]

from app.models.recommendation import Recommendation
from app.persistence.mongodb import collections as col
from app.persistence.mongodb.mappers import recommendation_mapper


class RecommendationRepository:
    """Async repository for Recommendation persistence.

    Args:
        db: Motor database handle injected at construction time.
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
        self._collection = db[col.RECOMMENDATIONS]

    async def create(self, recommendation: Recommendation) -> Recommendation:
        """Persist a new Recommendation.

        Args:
            recommendation: Fully constructed ``Recommendation`` domain model.

        Returns:
            The stored ``Recommendation`` (identity after insert).
        """
        document = recommendation_mapper.to_document(recommendation)
        await self._collection.insert_one(document)
        return recommendation

    async def get_by_id(self, recommendation_id: UUID) -> Recommendation | None:
        """Retrieve a Recommendation by its UUID.

        Args:
            recommendation_id: The UUID of the recommendation to fetch.

        Returns:
            The ``Recommendation`` if found, ``None`` otherwise.
        """
        raw = await self._collection.find_one({"_id": str(recommendation_id)})
        if raw is None:
            return None
        return recommendation_mapper.to_domain(raw)

    async def list(
        self,
        *,
        workspace_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Recommendation]:
        """Return recommendations scoped to a workspace, newest first.

        Args:
            workspace_id: Workspace filter.
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.

        Returns:
            List of ``Recommendation`` domain models ordered by ``created_at`` descending.
        """
        cursor = (
            self._collection
            .find({"workspace_id": str(workspace_id)})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return [recommendation_mapper.to_domain(doc) async for doc in cursor]

    async def update(self, recommendation: Recommendation) -> Recommendation | None:
        """Replace an existing Recommendation document.

        Args:
            recommendation: ``Recommendation`` with updated fields.

        Returns:
            The updated ``Recommendation`` or ``None`` if not found.
        """
        document = recommendation_mapper.to_document(recommendation)
        result = await self._collection.replace_one(
            {"_id": str(recommendation.id)},
            document,
        )
        if result.matched_count == 0:
            return None
        return recommendation

    async def delete(self, recommendation_id: UUID) -> bool:
        """Delete a Recommendation by its UUID.

        Args:
            recommendation_id: The UUID of the recommendation to delete.

        Returns:
            ``True`` if deleted, ``False`` if not found.
        """
        result = await self._collection.delete_one({"_id": str(recommendation_id)})
        return result.deleted_count > 0
