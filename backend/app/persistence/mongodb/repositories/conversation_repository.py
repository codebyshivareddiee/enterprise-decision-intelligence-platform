"""ConversationRepository — CRUD access for the ``conversations`` collection."""

from __future__ import annotations

from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase  # type: ignore[import-untyped]

from app.models.conversation import Conversation
from app.persistence.mongodb import collections as col
from app.persistence.mongodb.mappers import conversation_mapper


class ConversationRepository:
    """Async repository for Conversation persistence.

    Args:
        db: Motor database handle injected at construction time.
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
        self._collection = db[col.CONVERSATIONS]

    async def create(self, conversation: Conversation) -> Conversation:
        """Persist a new Conversation.

        Args:
            conversation: Fully constructed ``Conversation`` domain model.

        Returns:
            The stored ``Conversation`` (identity after insert).
        """
        document = conversation_mapper.to_document(conversation)
        await self._collection.insert_one(document)
        return conversation

    async def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        """Retrieve a Conversation by its UUID.

        Args:
            conversation_id: The UUID of the conversation to fetch.

        Returns:
            The ``Conversation`` if found, ``None`` otherwise.
        """
        raw = await self._collection.find_one({"_id": str(conversation_id)})
        if raw is None:
            return None
        return conversation_mapper.to_domain(raw)

    async def list(
        self,
        *,
        organization_id: UUID,
        workspace_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Conversation]:
        """Return conversations scoped to an organization and workspace, newest first.

        Args:
            organization_id: Owning organization filter.
            workspace_id: Workspace filter.
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.

        Returns:
            List of ``Conversation`` domain models ordered by ``created_at`` descending.
        """
        cursor = (
            self._collection.find(
                {
                    "organization_id": str(organization_id),
                    "workspace_id": str(workspace_id),
                }
            )
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return [conversation_mapper.to_domain(doc) async for doc in cursor]

    async def update(self, conversation: Conversation) -> Conversation | None:
        """Replace an existing Conversation document.

        Args:
            conversation: ``Conversation`` with updated fields (e.g. new messages appended).

        Returns:
            The updated ``Conversation`` or ``None`` if not found.
        """
        document = conversation_mapper.to_document(conversation)
        result = await self._collection.replace_one(
            {"_id": str(conversation.id)},
            document,
        )
        if result.matched_count == 0:
            return None
        return conversation

    async def delete(self, conversation_id: UUID) -> bool:
        """Delete a Conversation by its UUID.

        Args:
            conversation_id: The UUID of the conversation to delete.

        Returns:
            ``True`` if deleted, ``False`` if not found.
        """
        result = await self._collection.delete_one({"_id": str(conversation_id)})
        return result.deleted_count > 0
