"""LifecycleDefinitionRepository — CRUD access for the ``lifecycle_definitions`` collection."""

from __future__ import annotations

from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase  # type: ignore[import-untyped]

from app.models.lifecycle_definition import LifecycleDefinition
from app.persistence.mongodb import collections as col
from app.persistence.mongodb.mappers import lifecycle_definition_mapper


class LifecycleDefinitionRepository:
    """Async repository for LifecycleDefinition persistence.

    Args:
        db: Motor database handle injected at construction time.
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
        self._collection = db[col.LIFECYCLE_DEFINITIONS]

    async def create(self, lifecycle: LifecycleDefinition) -> LifecycleDefinition:
        """Persist a new LifecycleDefinition.

        Args:
            lifecycle: Fully constructed ``LifecycleDefinition`` domain model.

        Returns:
            The stored ``LifecycleDefinition`` (identity after insert).
        """
        document = lifecycle_definition_mapper.to_document(lifecycle)
        await self._collection.insert_one(document)
        return lifecycle

    async def get_by_id(self, lifecycle_id: UUID) -> LifecycleDefinition | None:
        """Retrieve a LifecycleDefinition by its UUID.

        Args:
            lifecycle_id: The UUID of the lifecycle to fetch.

        Returns:
            The ``LifecycleDefinition`` if found, ``None`` otherwise.
        """
        raw = await self._collection.find_one({"_id": str(lifecycle_id)})
        if raw is None:
            return None
        return lifecycle_definition_mapper.to_domain(raw)

    async def list(
        self,
        *,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[LifecycleDefinition]:
        """Return lifecycle definitions scoped to an organization.

        Args:
            organization_id: Required tenant filter.
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.

        Returns:
            List of ``LifecycleDefinition`` domain models.
        """
        cursor = (
            self._collection
            .find({"organization_id": str(organization_id)})
            .skip(skip)
            .limit(limit)
        )
        return [lifecycle_definition_mapper.to_domain(doc) async for doc in cursor]

    async def update(self, lifecycle: LifecycleDefinition) -> LifecycleDefinition | None:
        """Replace an existing LifecycleDefinition document.

        Args:
            lifecycle: ``LifecycleDefinition`` with updated fields.

        Returns:
            The updated ``LifecycleDefinition`` or ``None`` if not found.
        """
        document = lifecycle_definition_mapper.to_document(lifecycle)
        result = await self._collection.replace_one(
            {"_id": str(lifecycle.id)},
            document,
        )
        if result.matched_count == 0:
            return None
        return lifecycle

    async def delete(self, lifecycle_id: UUID) -> bool:
        """Delete a LifecycleDefinition by its UUID.

        Args:
            lifecycle_id: The UUID of the lifecycle to delete.

        Returns:
            ``True`` if deleted, ``False`` if not found.
        """
        result = await self._collection.delete_one({"_id": str(lifecycle_id)})
        return result.deleted_count > 0
