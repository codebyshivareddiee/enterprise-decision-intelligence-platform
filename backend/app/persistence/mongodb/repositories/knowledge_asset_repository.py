"""KnowledgeAssetRepository — CRUD access for the ``knowledge_assets`` collection.

KnowledgeAssets are organization-level resources. They carry no ``workspace_id``.
The workspace-to-asset selection relationship lives on the Workspace document
(``selected_knowledge_asset_ids``).

Query patterns
--------------
* ``list(organization_id)``       — browse the full org asset library.
* ``get_by_ids(organization_id, asset_ids)`` — fetch only the assets a
  workspace has selected; the caller passes ``workspace.selected_knowledge_asset_ids``.
  The ``organization_id`` filter is applied on every query as a hard tenant
  safety check: no asset can be returned that does not belong to the org.
"""

from __future__ import annotations

from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase  # type: ignore[import-untyped]

from app.models.knowledge_asset import KnowledgeAsset
from app.persistence.mongodb import collections as col
from app.persistence.mongodb.mappers import knowledge_asset_mapper


class KnowledgeAssetRepository:
    """Async repository for KnowledgeAsset persistence.

    All queries are scoped by ``organization_id`` to enforce tenant isolation.
    There is no ``workspace_id`` filter — assets are org-owned.

    Args:
        db: Motor database handle injected at construction time.
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
        self._collection = db[col.KNOWLEDGE_ASSETS]

    async def create(self, asset: KnowledgeAsset) -> KnowledgeAsset:
        """Persist a new KnowledgeAsset.

        Args:
            asset: Fully constructed ``KnowledgeAsset`` domain model.

        Returns:
            The stored ``KnowledgeAsset`` (identity after insert).
        """
        document = knowledge_asset_mapper.to_document(asset)
        await self._collection.insert_one(document)
        return asset

    async def get_by_id(self, asset_id: UUID) -> KnowledgeAsset | None:
        """Retrieve a KnowledgeAsset by its UUID.

        Args:
            asset_id: The UUID of the asset to fetch.

        Returns:
            The ``KnowledgeAsset`` if found, ``None`` otherwise.
        """
        raw = await self._collection.find_one({"_id": str(asset_id)})
        if raw is None:
            return None
        return knowledge_asset_mapper.to_domain(raw)

    async def get_by_ids(
        self,
        organization_id: UUID,
        asset_ids: list[UUID],
    ) -> list[KnowledgeAsset]:
        """Fetch a specific set of assets belonging to an organization.

        This is the primary workspace-contextual read method.  The caller
        passes ``workspace.selected_knowledge_asset_ids``; this method
        returns exactly those assets that exist AND belong to
        ``organization_id``.  Any IDs not found (deleted, wrong org) are
        silently omitted — the caller decides how to handle gaps.

        The result order matches the order of ``asset_ids`` as provided.

        Args:
            organization_id: Owning organization — applied as a hard
                tenant safety filter on every query.
            asset_ids: List of asset UUIDs to fetch (e.g., from
                ``Workspace.selected_knowledge_asset_ids``).

        Returns:
            List of ``KnowledgeAsset`` domain models, preserving the
            order of ``asset_ids``.
        """
        if not asset_ids:
            return []

        id_strings = [str(aid) for aid in asset_ids]
        cursor = self._collection.find(
            {
                "_id": {"$in": id_strings},
                "organization_id": str(organization_id),
            }
        )
        # Build a lookup so we can return results in the caller's order.
        raw_docs = {doc["_id"]: doc async for doc in cursor}
        return [
            knowledge_asset_mapper.to_domain(raw_docs[id_str])
            for id_str in id_strings
            if id_str in raw_docs
        ]

    async def list(
        self,
        *,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[KnowledgeAsset]:
        """Return all assets in an organization's library, paginated.

        Use this to browse the full org-level asset catalog.  To fetch
        only the assets a specific workspace has selected, use
        ``get_by_ids(organization_id, workspace.selected_knowledge_asset_ids)``
        instead.

        Args:
            organization_id: Required tenant filter.
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.

        Returns:
            List of ``KnowledgeAsset`` domain models.
        """
        cursor = (
            self._collection
            .find({"organization_id": str(organization_id)})
            .skip(skip)
            .limit(limit)
        )
        return [knowledge_asset_mapper.to_domain(doc) async for doc in cursor]

    async def update(self, asset: KnowledgeAsset) -> KnowledgeAsset | None:
        """Replace an existing KnowledgeAsset document.

        Args:
            asset: ``KnowledgeAsset`` with updated fields.

        Returns:
            The updated ``KnowledgeAsset`` or ``None`` if not found.
        """
        document = knowledge_asset_mapper.to_document(asset)
        result = await self._collection.replace_one(
            {"_id": str(asset.id)},
            document,
        )
        if result.matched_count == 0:
            return None
        return asset

    async def delete(self, asset_id: UUID) -> bool:
        """Delete a KnowledgeAsset by its UUID.

        Args:
            asset_id: The UUID of the asset to delete.

        Returns:
            ``True`` if deleted, ``False`` if not found.
        """
        result = await self._collection.delete_one({"_id": str(asset_id)})
        return result.deleted_count > 0

