"""MongoDB index definitions and startup initialisation.

Call ``create_all_indexes(db)`` once during application startup (after
``connect()`` has been awaited) to ensure all indexes exist.

Index philosophy:
- ``background=False`` is intentional: we create indexes at startup
  before the app starts serving traffic, so blocking is acceptable and
  avoids partial-index race conditions.
- All indexes use ``unique=False`` by default unless business rules
  explicitly require uniqueness.
- Compound indexes are listed left-to-right in selectivity order
  (highest-cardinality field first).
"""

from __future__ import annotations

import logging
from typing import Final

from motor.motor_asyncio import AsyncIOMotorDatabase  # type: ignore[import-untyped]
from pymongo import ASCENDING, IndexModel

from app.persistence.mongodb import collections as col

logger: Final = logging.getLogger(__name__)


async def create_all_indexes(db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
    """Create all application indexes in MongoDB.

    Uses ``create_indexes`` which is idempotent — re-running on an
    existing index is a no-op.  Safe to call on every startup.

    Args:
        db: The Motor database handle obtained from ``get_database()``.
    """
    await _create_organization_indexes(db)
    await _create_user_indexes(db)
    await _create_knowledge_schema_indexes(db)
    await _create_knowledge_asset_indexes(db)
    await _create_workspace_indexes(db)
    await _create_rule_indexes(db)
    await _create_conversation_indexes(db)
    await _create_recommendation_indexes(db)
    await _create_decision_history_indexes(db)
    await _create_preference_profile_indexes(db)

    logger.info("mongodb.indexes.all_created")


# ---------------------------------------------------------------------------
# Per-collection index helpers
# ---------------------------------------------------------------------------


async def _create_organization_indexes(db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
    """Organizations: name (unique), slug (unique)."""
    indexes = [
        IndexModel([("name", ASCENDING)], name="org_name", unique=True),
        IndexModel([("slug", ASCENDING)], name="org_slug", unique=True),
    ]
    await db[col.ORGANIZATIONS].create_indexes(indexes)
    logger.debug("mongodb.indexes.created", extra={"collection": col.ORGANIZATIONS})


async def _create_user_indexes(db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
    """Users: organization_id, email (unique within tenant), status."""
    indexes = [
        # Tenant-scoped user lookup (most common query pattern).
        IndexModel(
            [("organization_id", ASCENDING), ("email", ASCENDING)],
            name="user_org_email",
            unique=True,
        ),
        IndexModel([("organization_id", ASCENDING)], name="user_org_id"),
        IndexModel([("status", ASCENDING)], name="user_status"),
    ]
    await db[col.USERS].create_indexes(indexes)
    logger.debug("mongodb.indexes.created", extra={"collection": col.USERS})


async def _create_knowledge_schema_indexes(db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
    """Knowledge Schemas: organization_id."""
    indexes = [
        IndexModel([("organization_id", ASCENDING)], name="schema_org_id"),
    ]
    await db[col.KNOWLEDGE_SCHEMAS].create_indexes(indexes)
    logger.debug("mongodb.indexes.created", extra={"collection": col.KNOWLEDGE_SCHEMAS})


async def _create_knowledge_asset_indexes(db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
    """Knowledge Assets: organization_id (primary list key), schema_id, status.

    ``workspace_id`` does NOT appear here — assets are org-owned.  The
    workspace-to-asset relationship is stored in the workspaces collection.
    """
    indexes = [
        # Primary list query: all assets for an organization.
        IndexModel([("organization_id", ASCENDING)], name="asset_org_id"),
        # Useful when validating schema conformance across all org assets.
        IndexModel([("schema_id", ASCENDING)], name="asset_schema_id"),
        # Processing pipeline queries (e.g., find all PENDING assets).
        IndexModel([("status", ASCENDING)], name="asset_status"),
    ]
    await db[col.KNOWLEDGE_ASSETS].create_indexes(indexes)
    logger.debug("mongodb.indexes.created", extra={"collection": col.KNOWLEDGE_ASSETS})


async def _create_workspace_indexes(db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
    """Workspaces: org_id, status."""
    indexes = [
        IndexModel([("organization_id", ASCENDING)], name="workspace_org_id"),
        IndexModel(
            [("organization_id", ASCENDING), ("status", ASCENDING)],
            name="workspace_org_status",
        ),
    ]
    await db[col.WORKSPACES].create_indexes(indexes)
    logger.debug("mongodb.indexes.created", extra={"collection": col.WORKSPACES})


async def _create_rule_indexes(db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
    """Business Rules: org_id + workspace_id, rule_type, is_active."""
    indexes = [
        IndexModel(
            [("organization_id", ASCENDING), ("workspace_id", ASCENDING)],
            name="rule_org_workspace",
        ),
        IndexModel([("rule_type", ASCENDING)], name="rule_type"),
        IndexModel([("is_active", ASCENDING)], name="rule_is_active"),
        # Sort by priority within a workspace.
        IndexModel(
            [("workspace_id", ASCENDING), ("priority", ASCENDING)],
            name="rule_workspace_priority",
        ),
    ]
    await db[col.RULES].create_indexes(indexes)
    logger.debug("mongodb.indexes.created", extra={"collection": col.RULES})


async def _create_conversation_indexes(db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
    """Conversations: org_id + workspace_id, user_id, is_active."""
    indexes = [
        IndexModel(
            [("organization_id", ASCENDING), ("workspace_id", ASCENDING)],
            name="conv_org_workspace",
        ),
        IndexModel([("user_id", ASCENDING)], name="conv_user_id"),
        IndexModel([("is_active", ASCENDING)], name="conv_is_active"),
    ]
    await db[col.CONVERSATIONS].create_indexes(indexes)
    logger.debug("mongodb.indexes.created", extra={"collection": col.CONVERSATIONS})


async def _create_recommendation_indexes(db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
    """Recommendations: workspace_id, status, triggered_by."""
    indexes = [
        IndexModel([("workspace_id", ASCENDING)], name="rec_workspace_id"),
        IndexModel(
            [("workspace_id", ASCENDING), ("status", ASCENDING)],
            name="rec_workspace_status",
        ),
        IndexModel([("triggered_by", ASCENDING)], name="rec_triggered_by"),
    ]
    await db[col.RECOMMENDATIONS].create_indexes(indexes)
    logger.debug("mongodb.indexes.created", extra={"collection": col.RECOMMENDATIONS})


async def _create_decision_history_indexes(db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
    """Decision History: workspace_id, recommendation_id, asset_id.

    Decision History is append-only; no unique constraints beyond the
    document _id.
    """
    indexes = [
        IndexModel([("workspace_id", ASCENDING)], name="dh_workspace_id"),
        IndexModel([("recommendation_id", ASCENDING)], name="dh_recommendation_id"),
        # Compound for the Learner's most common read pattern.
        IndexModel(
            [("workspace_id", ASCENDING), ("recommendation_id", ASCENDING)],
            name="dh_workspace_recommendation",
        ),
        IndexModel([("asset_id", ASCENDING)], name="dh_asset_id"),
        IndexModel([("decided_by", ASCENDING)], name="dh_decided_by"),
    ]
    await db[col.DECISION_HISTORY].create_indexes(indexes)
    logger.debug("mongodb.indexes.created", extra={"collection": col.DECISION_HISTORY})


async def _create_preference_profile_indexes(db: AsyncIOMotorDatabase) -> None:  # type: ignore[type-arg]
    """Preference Profiles: workspace_id (unique per workspace), org_id."""
    indexes = [
        # One profile per workspace — enforced at the application layer,
        # but the unique index provides a hard guarantee.
        IndexModel(
            [("workspace_id", ASCENDING)],
            name="pp_workspace_id",
            unique=True,
        ),
        IndexModel([("organization_id", ASCENDING)], name="pp_org_id"),
    ]
    await db[col.PREFERENCE_PROFILES].create_indexes(indexes)
    logger.debug(
        "mongodb.indexes.created", extra={"collection": col.PREFERENCE_PROFILES}
    )
