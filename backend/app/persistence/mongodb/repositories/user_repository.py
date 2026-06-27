"""UserRepository — CRUD access for the ``users`` collection."""

from __future__ import annotations

from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase  # type: ignore[import-untyped]

from app.models.user import User
from app.persistence.mongodb import collections as col
from app.persistence.mongodb.mappers import user_mapper


class UserRepository:
    """Async repository for User persistence.

    Args:
        db: Motor database handle injected at construction time.
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
        self._collection = db[col.USERS]

    async def create(self, user: User) -> User:
        """Persist a new User.

        Args:
            user: Fully constructed ``User`` domain model.

        Returns:
            The stored ``User`` (identity after insert).
        """
        document = user_mapper.to_document(user)
        await self._collection.insert_one(document)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Retrieve a User by its UUID.

        Args:
            user_id: The UUID of the user to fetch.

        Returns:
            The ``User`` if found, ``None`` otherwise.
        """
        raw = await self._collection.find_one({"_id": str(user_id)})
        if raw is None:
            return None
        return user_mapper.to_domain(raw)

    async def list(
        self,
        *,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """Return a paginated list of Users scoped to an organization.

        All user queries must be scoped by ``organization_id`` to enforce
        tenant isolation (see DO_NOT_CHANGE.md).

        Args:
            organization_id: Owning organization — used as a required filter.
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.

        Returns:
            List of ``User`` domain models.
        """
        cursor = (
            self._collection
            .find({"organization_id": str(organization_id)})
            .skip(skip)
            .limit(limit)
        )
        return [user_mapper.to_domain(doc) async for doc in cursor]

    async def update(self, user: User) -> User | None:
        """Replace an existing User document.

        Args:
            user: ``User`` with updated fields.

        Returns:
            The updated ``User`` or ``None`` if not found.
        """
        document = user_mapper.to_document(user)
        result = await self._collection.replace_one(
            {"_id": str(user.id)},
            document,
        )
        if result.matched_count == 0:
            return None
        return user

    async def delete(self, user_id: UUID) -> bool:
        """Delete a User by its UUID.

        Args:
            user_id: The UUID of the user to delete.

        Returns:
            ``True`` if deleted, ``False`` if not found.
        """
        result = await self._collection.delete_one({"_id": str(user_id)})
        return result.deleted_count > 0
