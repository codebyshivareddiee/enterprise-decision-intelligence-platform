"""BusinessRuleRepository — CRUD access for the ``rules`` collection."""

from __future__ import annotations

from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase  # type: ignore[import-untyped]

from app.models.business_rule import BusinessRule
from app.persistence.mongodb import collections as col
from app.persistence.mongodb.mappers import business_rule_mapper


class BusinessRuleRepository:
    """Async repository for BusinessRule persistence.

    Args:
        db: Motor database handle injected at construction time.
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
        self._collection = db[col.RULES]

    async def create(self, rule: BusinessRule) -> BusinessRule:
        """Persist a new BusinessRule.

        Args:
            rule: Fully constructed ``BusinessRule`` domain model.

        Returns:
            The stored ``BusinessRule`` (identity after insert).
        """
        document = business_rule_mapper.to_document(rule)
        await self._collection.insert_one(document)
        return rule

    async def get_by_id(self, rule_id: UUID) -> BusinessRule | None:
        """Retrieve a BusinessRule by its UUID.

        Args:
            rule_id: The UUID of the rule to fetch.

        Returns:
            The ``BusinessRule`` if found, ``None`` otherwise.
        """
        raw = await self._collection.find_one({"_id": str(rule_id)})
        if raw is None:
            return None
        return business_rule_mapper.to_domain(raw)

    async def list(
        self,
        *,
        organization_id: UUID,
        workspace_id: UUID,
        skip: int = 0,
        limit: int = 200,
    ) -> list[BusinessRule]:
        """Return rules scoped to an organization and workspace, ordered by priority.

        Args:
            organization_id: Owning organization filter.
            workspace_id: Workspace filter.
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.

        Returns:
            List of ``BusinessRule`` domain models ordered by ``priority`` ascending.
        """
        cursor = (
            self._collection.find(
                {
                    "organization_id": str(organization_id),
                    "workspace_id": str(workspace_id),
                }
            )
            .sort("priority", 1)
            .skip(skip)
            .limit(limit)
        )
        return [business_rule_mapper.to_domain(doc) async for doc in cursor]

    async def update(self, rule: BusinessRule) -> BusinessRule | None:
        """Replace an existing BusinessRule document.

        Args:
            rule: ``BusinessRule`` with updated fields.

        Returns:
            The updated ``BusinessRule`` or ``None`` if not found.
        """
        document = business_rule_mapper.to_document(rule)
        result = await self._collection.replace_one(
            {"_id": str(rule.id)},
            document,
        )
        if result.matched_count == 0:
            return None
        return rule

    async def delete(self, rule_id: UUID) -> bool:
        """Delete a BusinessRule by its UUID.

        Args:
            rule_id: The UUID of the rule to delete.

        Returns:
            ``True`` if deleted, ``False`` if not found.
        """
        result = await self._collection.delete_one({"_id": str(rule_id)})
        return result.deleted_count > 0
