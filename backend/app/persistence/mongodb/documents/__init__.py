"""MongoDB document type definitions.

Each module defines a ``TypedDict`` that mirrors the raw BSON document
stored in MongoDB.  These are **not** domain models — they are the
persistence schema.  Mappers convert between documents and domain models.

Rules:
- UUIDs are stored as strings (str) for cross-driver portability.
- Datetimes are stored as datetime objects (Motor auto-converts to BSON
  Date).
- Nested value objects are represented as plain dicts.
- ``_id`` always contains the entity UUID string.
"""
