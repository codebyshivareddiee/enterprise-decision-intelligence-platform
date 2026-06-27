"""WorkspaceRepository — CRUD access for the ``workspaces`` collection."""

from __future__ import annotations

from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase  # type: ignore[import-untyped]

from app.models.workspace import Workspace
from app.persistence.mongodb import collections as col
from app.persistence.mongodb.mappers import workspace_mapper


class WorkspaceRepository:
    """Async repository for Workspace persistence.

    Args:
        db: Motor database handle injected at construction time.
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
        self._collection = db[col.WORKSPACES]

    async def create(self, workspace: Workspace) -> Workspace:
        """Persist a new Workspace.

        Args:
            workspace: Fully constructed ``Workspace`` domain model.

        Returns:
            The stored ``Workspace`` (identity after insert).
        """
        document = workspace_mapper.to_document(workspace)
        await self._collection.insert_one(document)
        return workspace

    async def get_by_id(self, workspace_id: UUID) -> Workspace | None:
        """Retrieve a Workspace by its UUID.

        Args:
            workspace_id: The UUID of the workspace to fetch.

        Returns:
            The ``Workspace`` if found, ``None`` otherwise.
        """
        raw = await self._collection.find_one({"_id": str(workspace_id)})
        if raw is None:
            return None
        return workspace_mapper.to_domain(raw)

    async def list(
        self,
        *,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Workspace]:
        """Return workspaces scoped to an organization.

        Args:
            organization_id: Required tenant filter.
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.

        Returns:
            List of ``Workspace`` domain models.
        """
        cursor = (
            self._collection
            .find({"organization_id": str(organization_id)})
            .skip(skip)
            .limit(limit)
        )
        return [workspace_mapper.to_domain(doc) async for doc in cursor]

    async def update(self, workspace: Workspace) -> Workspace | None:
        """Replace an existing Workspace document.

        Args:
            workspace: ``Workspace`` with updated fields.

        Returns:
            The updated ``Workspace`` or ``None`` if not found.
        """
        document = workspace_mapper.to_document(workspace)
        result = await self._collection.replace_one(
            {"_id": str(workspace.id)},
            document,
        )
        if result.matched_count == 0:
            return None
        return workspace

    async def delete(self, workspace_id: UUID) -> bool:
        """Delete a Workspace by its UUID.

        Args:
            workspace_id: The UUID of the workspace to delete.

        Returns:
            ``True`` if deleted, ``False`` if not found.
        """
        result = await self._collection.delete_one({"_id": str(workspace_id)})
        return result.deleted_count > 0
