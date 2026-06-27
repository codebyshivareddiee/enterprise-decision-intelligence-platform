"""BusinessRule mapper — Domain ↔ Mongo document."""

from __future__ import annotations

from uuid import UUID

from app.models.business_rule import BusinessRule, RuleCondition
from app.models.enums import RuleOperator, RuleType
from app.persistence.mongodb.documents.business_rule_document import (
    BusinessRuleDocument,
    RuleConditionDocument,
)

# ---------------------------------------------------------------------------
# RuleCondition helpers
# ---------------------------------------------------------------------------


def _condition_to_document(cond: RuleCondition) -> RuleConditionDocument:
    return RuleConditionDocument(
        field_name=cond.field_name,
        operator=cond.operator.value,
        value=cond.value,
    )


def _condition_to_domain(doc: RuleConditionDocument) -> RuleCondition:
    return RuleCondition(
        field_name=doc["field_name"],
        operator=RuleOperator(doc["operator"]),
        value=doc["value"],
    )


# ---------------------------------------------------------------------------
# BusinessRule mapper
# ---------------------------------------------------------------------------


def to_document(rule: BusinessRule) -> BusinessRuleDocument:
    """Convert a ``BusinessRule`` domain model to a Mongo document."""
    return BusinessRuleDocument(
        _id=str(rule.id),
        organization_id=str(rule.organization_id),
        workspace_id=str(rule.workspace_id),
        name=rule.name,
        description=rule.description,
        rule_type=rule.rule_type.value,
        conditions=[_condition_to_document(c) for c in rule.conditions],
        is_active=rule.is_active,
        weight=rule.weight,
        priority=rule.priority,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def to_domain(doc: BusinessRuleDocument) -> BusinessRule:
    """Convert a raw Mongo document to a ``BusinessRule`` domain model."""
    return BusinessRule(
        id=UUID(doc["_id"]),
        organization_id=UUID(doc["organization_id"]),
        workspace_id=UUID(doc["workspace_id"]),
        name=doc["name"],
        description=doc["description"],
        rule_type=RuleType(doc["rule_type"]),
        conditions=[_condition_to_domain(c) for c in doc["conditions"]],
        is_active=doc["is_active"],
        weight=doc["weight"],
        priority=doc["priority"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )
