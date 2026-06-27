"""BusinessRule MongoDB document schema."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from typing_extensions import TypedDict


class RuleConditionDocument(TypedDict):
    """Embedded sub-document for a single rule condition."""

    field_name: str
    operator: str  # RuleOperator enum value
    value: Any  # Scalar, list, or None depending on operator


class BusinessRuleDocument(TypedDict):
    """Raw BSON document stored in the ``rules`` collection."""

    _id: str  # UUID v4 as string
    organization_id: str
    workspace_id: str
    name: str
    description: str | None
    rule_type: str  # RuleType enum value
    conditions: list[RuleConditionDocument]
    is_active: bool
    weight: float
    priority: int
    created_at: datetime
    updated_at: datetime
