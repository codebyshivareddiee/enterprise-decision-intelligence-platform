"""PreferenceProfileRepository — CRUD access for the ``preference_profiles`` collection.

There is at most one PreferenceProfile per workspace (enforced by the unique
index on ``workspace_id``). The Learner is the only writer.
"""

from __future__ import annotations

from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase  # type: ignore[import-untyped]

from app.models.preference_profile import PreferenceProfile
from app.persistence.mongodb import collections as col
from app.persistence.mongodb.mappers import preference_profile_mapper


class PreferenceProfileRepository:
    """Async repository for PreferenceProfile persistence.

    Args:
        db: Motor database handle injected at construction time.
    """

    def __init__(self, db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
        self._collection = db[col.PREFERENCE_PROFILES]

    async def create(self, profile: PreferenceProfile) -> PreferenceProfile:
        """Persist a new PreferenceProfile.

        Args:
            profile: Fully constructed ``PreferenceProfile`` domain model.

        Returns:
            The stored ``PreferenceProfile`` (identity after insert).
        """
        document = preference_profile_mapper.to_document(profile)
        await self._collection.insert_one(document)
        return profile

    async def get_by_id(self, profile_id: UUID) -> PreferenceProfile | None:
        """Retrieve a PreferenceProfile by its UUID.

        Args:
            profile_id: The UUID of the profile to fetch.

        Returns:
            The ``PreferenceProfile`` if found, ``None`` otherwise.
        """
        raw = await self._collection.find_one({"_id": str(profile_id)})
        if raw is None:
            return None
        return preference_profile_mapper.to_domain(raw)

    async def get_by_workspace_id(self, workspace_id: UUID) -> PreferenceProfile | None:
        """Retrieve the unique PreferenceProfile for a workspace.

        There is at most one profile per workspace.  This is the primary
        read access pattern used by the Learner and the Reasoning Agent.

        Args:
            workspace_id: The UUID of the workspace whose profile to fetch.

        Returns:
            The ``PreferenceProfile`` if it exists, ``None`` otherwise.
        """
        raw = await self._collection.find_one({"workspace_id": str(workspace_id)})
        if raw is None:
            return None
        return preference_profile_mapper.to_domain(raw)

    async def list(
        self,
        *,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[PreferenceProfile]:
        """Return preference profiles scoped to an organization.

        Args:
            organization_id: Required tenant filter.
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.

        Returns:
            List of ``PreferenceProfile`` domain models.
        """
        cursor = (
            self._collection
            .find({"organization_id": str(organization_id)})
            .skip(skip)
            .limit(limit)
        )
        return [preference_profile_mapper.to_domain(doc) async for doc in cursor]

    async def update(self, profile: PreferenceProfile) -> PreferenceProfile | None:
        """Replace an existing PreferenceProfile document.

        Args:
            profile: ``PreferenceProfile`` with updated fields.

        Returns:
            The updated ``PreferenceProfile`` or ``None`` if not found.
        """
        document = preference_profile_mapper.to_document(profile)
        result = await self._collection.replace_one(
            {"_id": str(profile.id)},
            document,
        )
        if result.matched_count == 0:
            return None
        return profile

    async def delete(self, profile_id: UUID) -> bool:
        """Delete a PreferenceProfile by its UUID.

        Args:
            profile_id: The UUID of the profile to delete.

        Returns:
            ``True`` if deleted, ``False`` if not found.
        """
        result = await self._collection.delete_one({"_id": str(profile_id)})
        return result.deleted_count > 0
