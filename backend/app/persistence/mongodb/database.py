"""Database accessor.

Returns the Motor ``AsyncIOMotorDatabase`` for the configured database
name.  Repositories import ``get_database()`` to obtain a handle to
their collections.

No FastAPI ``Depends`` wiring here — that is added in the API layer
(P13).  At this stage, repositories receive the database via
constructor injection.
"""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase  # type: ignore[import-untyped]

from app.config.settings import get_settings
from app.persistence.mongodb.client import get_mongo_client


def get_database() -> AsyncIOMotorDatabase:  # type: ignore[type-arg]
    """Return the Motor database for the configured database name.

    The database name is read from ``settings.mongodb_db_name``.  This
    function is intentionally synchronous — Motor's ``get_database()``
    call is cheap and non-blocking.

    Returns:
        An ``AsyncIOMotorDatabase`` scoped to the application database.
    """
    settings = get_settings()
    client = get_mongo_client()
    return client[settings.mongodb_db_name]
