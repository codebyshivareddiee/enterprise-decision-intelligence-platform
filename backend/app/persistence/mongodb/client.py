"""MongoDB connection manager.

Provides a single Motor ``AsyncIOMotorClient`` for the application
lifetime.  The client is created once on startup and closed on shutdown.

Usage
-----
Call ``connect()`` in the application lifespan startup hook and
``disconnect()`` in the shutdown hook.  All other modules obtain the
client via ``get_mongo_client()``.

No FastAPI wiring lives here — that belongs in the API layer (P13).
"""

from __future__ import annotations

import logging
from typing import Final

from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore[import-untyped]

logger: Final = logging.getLogger(__name__)

# Module-level singleton — intentionally not a class so that the module
# itself acts as the registry.  There is only ever one Mongo client per
# process.
_client: AsyncIOMotorClient | None = None  # type: ignore[type-arg]


async def connect(uri: str, *, server_selection_timeout_ms: int = 5_000) -> None:
    """Create the Motor client and verify connectivity.

    Args:
        uri: MongoDB Atlas connection string (from settings).
        server_selection_timeout_ms: How long Motor waits before giving
            up on a server selection attempt.  Defaults to 5 s which is
            aggressive enough to fail fast in local dev.

    Raises:
        RuntimeError: If ``connect()`` is called more than once without
            an intervening ``disconnect()``.
    """
    global _client  # noqa: PLW0603

    if _client is not None:
        raise RuntimeError(
            "MongoDB client is already connected. "
            "Call disconnect() before re-connecting."
        )

    logger.info("mongodb.connecting", extra={"uri": _redact_uri(uri)})
    _client = AsyncIOMotorClient(
        uri,
        serverSelectionTimeoutMS=server_selection_timeout_ms,
    )

    # Ping the deployment to validate credentials and connectivity.
    await _client.admin.command("ping")
    logger.info("mongodb.connected")


async def disconnect() -> None:
    """Close the Motor client and release all connections.

    Safe to call even if the client was never connected (no-op).
    """
    global _client  # noqa: PLW0603

    if _client is None:
        logger.warning("mongodb.disconnect_called_but_not_connected")
        return

    _client.close()
    _client = None
    logger.info("mongodb.disconnected")


def get_mongo_client() -> AsyncIOMotorClient:  # type: ignore[type-arg]
    """Return the active Motor client.

    Raises:
        RuntimeError: If called before ``connect()`` has been awaited.
    """
    if _client is None:
        raise RuntimeError(
            "MongoDB client is not initialised. "
            "Ensure connect() has been awaited during application startup."
        )
    return _client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _redact_uri(uri: str) -> str:
    """Replace the password segment of a MongoDB URI with ``****``."""
    try:
        # The URI may be in the form:
        #   mongodb+srv://user:password@host/db
        # We only log up to and including the username.
        at_index = uri.index("@")
        scheme_end = uri.index("://") + 3
        credentials = uri[scheme_end:at_index]
        if ":" in credentials:
            user = credentials.split(":")[0]
            return uri[:scheme_end] + user + ":****@" + uri[at_index + 1 :]
    except ValueError:
        pass
    return uri
