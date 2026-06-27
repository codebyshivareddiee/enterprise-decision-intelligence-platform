"""MongoDB collection name constants.

All collection names used by repositories are defined here as module-level
string constants.  Never hard-code a collection name inside a repository
or query — always import from this module.

Naming convention: singular snake_case matching the domain concept.
"""

from __future__ import annotations

from typing import Final

# ---------------------------------------------------------------------------
# Collection names
# ---------------------------------------------------------------------------

ORGANIZATIONS: Final[str] = "organizations"
USERS: Final[str] = "users"
KNOWLEDGE_SCHEMAS: Final[str] = "knowledge_schemas"
KNOWLEDGE_ASSETS: Final[str] = "knowledge_assets"
WORKSPACES: Final[str] = "workspaces"
RULES: Final[str] = "rules"
AGENTS: Final[str] = "agents"
CONVERSATIONS: Final[str] = "conversations"
RECOMMENDATIONS: Final[str] = "recommendations"
DECISION_HISTORY: Final[str] = "decision_history"
PREFERENCE_PROFILES: Final[str] = "preference_profiles"

# Convenience tuple for iteration (e.g., in tests or admin tooling).
ALL_COLLECTIONS: Final[tuple[str, ...]] = (
    ORGANIZATIONS,
    USERS,
    KNOWLEDGE_SCHEMAS,
    KNOWLEDGE_ASSETS,
    WORKSPACES,
    RULES,
    AGENTS,
    CONVERSATIONS,
    RECOMMENDATIONS,
    DECISION_HISTORY,
    PREFERENCE_PROFILES,
)
