"""KnowledgeSchemaRepository — CRUD access for the ``knowledge_schemas`` collection."""

from __future__ import annotations

from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase  # type: ignore[import-untyped]

from app.models.knowledge_schema import KnowledgeSchema
from app.persistence.mongodb import collections as col
from app.persistence.mongodb.mappers import knowledge_schema_mapper


class KnowledgeSchemaRepository:
    """Async repository for KnowledgeSchema persistence.

    Args:
        db: Motor database handle injected at construction time.
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
        self._collection = db[col.KNOWLEDGE_SCHEMAS]

    async def create(self, schema: KnowledgeSchema) -> KnowledgeSchema:
        """Persist a new KnowledgeSchema.

        Args:
            schema: Fully constructed ``KnowledgeSchema`` domain model.

        Returns:
            The stored ``KnowledgeSchema`` (identity after insert).
        """
        document = knowledge_schema_mapper.to_document(schema)
        await self._collection.insert_one(document)
        return schema

    async def get_by_id(self, schema_id: UUID) -> KnowledgeSchema | None:
        """Retrieve a KnowledgeSchema by its UUID.

        Args:
            schema_id: The UUID of the schema to fetch.

        Returns:
            The ``KnowledgeSchema`` if found, ``None`` otherwise.
        """
        raw = await self._collection.find_one({"_id": str(schema_id)})
        if raw is None:
            return None
        return knowledge_schema_mapper.to_domain(raw)

    async def list(
        self,
        *,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[KnowledgeSchema]:
        """Return schemas scoped to an organization.

        Args:
            organization_id: Required tenant filter.
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.

        Returns:
            List of ``KnowledgeSchema`` domain models.
        """
        cursor = (
            self._collection
            .find({"organization_id": str(organization_id)})
            .skip(skip)
            .limit(limit)
        )
        return [knowledge_schema_mapper.to_domain(doc) async for doc in cursor]

    async def update(self, schema: KnowledgeSchema) -> KnowledgeSchema | None:
        """Replace an existing KnowledgeSchema document.

        Args:
            schema: ``KnowledgeSchema`` with updated fields.

        Returns:
            The updated ``KnowledgeSchema`` or ``None`` if not found.
        """
        document = knowledge_schema_mapper.to_document(schema)
        result = await self._collection.replace_one(
            {"_id": str(schema.id)},
            document,
        )
        if result.matched_count == 0:
            return None
        return schema

    async def delete(self, schema_id: UUID) -> bool:
        """Delete a KnowledgeSchema by its UUID.

        Args:
            schema_id: The UUID of the schema to delete.

        Returns:
            ``True`` if deleted, ``False`` if not found.
        """
        result = await self._collection.delete_one({"_id": str(schema_id)})
        return result.deleted_count > 0
