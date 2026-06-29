"""UserRepository — CRUD access for the ``users`` collection."""

from __future__ import annotations
from typing import Optional
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.auth.models import User
from app.persistence.mongodb import collections as col
from app.persistence.mongodb.mappers import user_mapper


class UserRepository:
    """Async repository for User persistence."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._collection = db[col.USERS]

    async def create(self, user: User) -> User:
        document = user_mapper.to_document(user)
        await self._collection.insert_one(document)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        raw = await self._collection.find_one({"_id": str(user_id)})
        if raw is None:
            return None
        return user_mapper.to_domain(raw)

    async def get_by_email(self, email: str) -> User | None:
        raw = await self._collection.find_one({"email": email})
        if raw is None:
            return None
        return user_mapper.to_domain(raw)

    async def update(self, user: User) -> User | None:
        document = user_mapper.to_document(user)
        result = await self._collection.replace_one(
            {"_id": str(user.id)},
            document,
        )
        if result.matched_count == 0:
            return None
        return user

    async def list(
        self,
        *,
        organization_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        query = {}
        if organization_id:
            query["organization_ids"] = str(organization_id)
        cursor = self._collection.find(query).skip(skip).limit(limit)
        return [user_mapper.to_domain(doc) async for doc in cursor]

    async def delete(self, user_id: UUID) -> bool:
        result = await self._collection.delete_one({"_id": str(user_id)})
        return result.deleted_count > 0
