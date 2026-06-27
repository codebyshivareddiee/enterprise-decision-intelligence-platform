"""OrganizationRepository — CRUD access for the ``organizations`` collection."""

from __future__ import annotations

from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase  # type: ignore[import-untyped]

from app.models.organization import Organization
from app.persistence.mongodb import collections as col
from app.persistence.mongodb.mappers import organization_mapper


class OrganizationRepository:
    """Async repository for Organization persistence.

    All methods are async and delegate to Motor.  No business logic lives
    here — validation and rules belong in the service layer.

    Args:
        db: Motor database handle injected at construction time.
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
        self._collection = db[col.ORGANIZATIONS]

    async def create(self, org: Organization) -> Organization:
        """Persist a new Organization and return the stored domain model.

        Args:
            org: Fully constructed ``Organization`` domain model.

        Returns:
            The same ``Organization`` as passed in (identity after insert).
        """
        document = organization_mapper.to_document(org)
        await self._collection.insert_one(document)
        return org

    async def get_by_id(self, org_id: UUID) -> Organization | None:
        """Retrieve an Organization by its UUID.

        Args:
            org_id: The UUID of the organization to fetch.

        Returns:
            The ``Organization`` if found, ``None`` otherwise.
        """
        raw = await self._collection.find_one({"_id": str(org_id)})
        if raw is None:
            return None
        return organization_mapper.to_domain(raw)

    async def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Organization]:
        """Return a paginated list of all Organizations.

        Args:
            skip: Number of documents to skip (offset).
            limit: Maximum number of documents to return.

        Returns:
            List of ``Organization`` domain models.
        """
        cursor = self._collection.find({}).skip(skip).limit(limit)
        return [organization_mapper.to_domain(doc) async for doc in cursor]

    async def update(self, org: Organization) -> Organization | None:
        """Replace an existing Organization document.

        Args:
            org: ``Organization`` with updated fields.  ``id`` is used to
                locate the existing document.

        Returns:
            The updated ``Organization`` if the document existed,
            ``None`` if no document with that ID was found.
        """
        document = organization_mapper.to_document(org)
        result = await self._collection.replace_one(
            {"_id": str(org.id)},
            document,
        )
        if result.matched_count == 0:
            return None
        return org

    async def delete(self, org_id: UUID) -> bool:
        """Delete an Organization by its UUID.

        Args:
            org_id: The UUID of the organization to delete.

        Returns:
            ``True`` if a document was deleted, ``False`` if not found.
        """
        result = await self._collection.delete_one({"_id": str(org_id)})
        return result.deleted_count > 0
