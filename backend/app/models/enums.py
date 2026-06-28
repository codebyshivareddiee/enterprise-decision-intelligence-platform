"""Shared domain enumerations.

All enums used across more than one domain model live here to prevent
circular imports. Keep this module free of business logic.
"""

from enum import Enum

# ---------------------------------------------------------------------------
# Organization & User
# ---------------------------------------------------------------------------


class UserRole(str, Enum):
    """Roles a user may hold within an organization."""

    OWNER = "owner"
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    """Lifecycle status of a user account."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    INVITED = "invited"
    SUSPENDED = "suspended"


# ---------------------------------------------------------------------------
# Workspace
# ---------------------------------------------------------------------------


class WorkspaceStatus(str, Enum):
    """Operational status of a workspace."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"


# ---------------------------------------------------------------------------
# Knowledge
# ---------------------------------------------------------------------------


class FieldType(str, Enum):
    """Supported field types within a KnowledgeSchema field definition."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    LIST = "list"
    OBJECT = "object"


class AssetStatus(str, Enum):
    """Processing / availability status of a knowledge asset."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class AssetContentType(str, Enum):
    """MIME-style content type categories for uploaded assets."""

    PDF = "pdf"
    DOCX = "docx"
    TEXT = "text"
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    STRUCTURED = "structured"  # Manually supplied structured record


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


class LifecycleStatus(str, Enum):
    """Status a entity / item occupies within a lifecycle stage."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    OVERRIDDEN = "overridden"


# ---------------------------------------------------------------------------
# Business Rules
# ---------------------------------------------------------------------------


class RuleType(str, Enum):
    """Classification of a business rule by its evaluation strategy."""

    HARD_FILTER = "hard_filter"  # Binary pass/fail — never overridable by AI
    SOFT_PREFERENCE = "soft_preference"  # Influences scoring but does not exclude
    MANDATORY_FIELD = "mandatory_field"  # Field presence / non-null requirement
    THRESHOLD = "threshold"  # Numeric comparison against a threshold


class RuleOperator(str, Enum):
    """Comparison operators used in threshold and filter rules."""

    EQ = "eq"  # Equal
    NEQ = "neq"  # Not equal
    GT = "gt"  # Greater than
    GTE = "gte"  # Greater than or equal
    LT = "lt"  # Less than
    LTE = "lte"  # Less than or equal
    IN = "in"  # Value in set
    NOT_IN = "not_in"  # Value not in set
    EXISTS = "exists"  # Field is present and non-null


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------


class RecommendationStatus(str, Enum):
    """State of a recommendation workflow run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------------


class DecisionOutcome(str, Enum):
    """The human decision made on a recommended entity / option."""

    APPROVED = "approved"
    REJECTED = "rejected"
    OVERRIDDEN = "overridden"  # AI recommended against; human approved anyway
    DEFERRED = "deferred"  # Decision postponed


# ---------------------------------------------------------------------------
# Learning
# ---------------------------------------------------------------------------


class LearningScope(str, Enum):
    """Scope at which a preference signal is applied."""

    WORKSPACE = (
        "workspace"  # Scoped to a single workspace (invariant from DO_NOT_CHANGE.md)
    )
    FIELD = "field"  # Preference tied to a specific schema field
    RULE = "rule"  # Preference tied to a specific business rule


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------


class MessageRole(str, Enum):
    """Role of the author in a conversation turn."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
