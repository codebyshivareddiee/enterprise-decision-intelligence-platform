"""Domain models package — pure Pydantic business entities (P2).

Import order is deliberately bottom-up (most fundamental first) to
make the dependency graph clear and to avoid any risk of circular
imports:

    enums → base → leaf models → models with nested value objects

All public symbols are re-exported here so callers can write:

    from app.models import Organization, User, WorkspaceStatus

instead of reaching into individual sub-modules.
"""

# -- Enumerations (no dependencies) ----------------------------------------
from app.models.enums import (
    AssetContentType,
    AssetStatus,
    DecisionOutcome,
    FieldType,
    LearningScope,
    LifecycleStatus,
    MessageRole,
    RecommendationStatus,
    RuleOperator,
    RuleType,
    UserRole,
    UserStatus,
    WorkspaceStatus,
)

# -- Base model (depends only on stdlib) ------------------------------------
from app.models.base import AuditedModel

# -- Leaf domain models (depend on enums + base) ----------------------------
from app.models.organization import Organization
from app.models.user import User
from app.models.workspace import Workspace

# -- Models with nested value objects (depend on enums + base + stdlib) -----
from app.models.knowledge_schema import KnowledgeSchema, SchemaField
from app.models.knowledge_asset import KnowledgeAsset
from app.models.lifecycle_definition import LifecycleDefinition, LifecycleStage
from app.models.business_rule import BusinessRule, RuleCondition
from app.models.recommendation import CandidateScore, Recommendation, RuleEvaluationResult
from app.models.decision_history import DecisionHistory
from app.models.preference_profile import PreferenceProfile, PreferenceSignal
from app.models.conversation import Conversation, ConversationMessage

__all__: list[str] = [
    # Enums
    "AssetContentType",
    "AssetStatus",
    "DecisionOutcome",
    "FieldType",
    "LearningScope",
    "LifecycleStatus",
    "MessageRole",
    "RecommendationStatus",
    "RuleOperator",
    "RuleType",
    "UserRole",
    "UserStatus",
    "WorkspaceStatus",
    # Base
    "AuditedModel",
    # Domain models
    "Organization",
    "User",
    "Workspace",
    "KnowledgeSchema",
    "SchemaField",
    "KnowledgeAsset",
    "LifecycleDefinition",
    "LifecycleStage",
    "BusinessRule",
    "RuleCondition",
    "CandidateScore",
    "Recommendation",
    "RuleEvaluationResult",
    "DecisionHistory",
    "PreferenceProfile",
    "PreferenceSignal",
    "Conversation",
    "ConversationMessage",
]
