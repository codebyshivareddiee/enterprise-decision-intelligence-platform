"""Deterministic Rule Evaluation Engine."""

from typing import Any

from app.models.business_rule import BusinessRule
from app.models.enums import RuleOperator


class RuleEngine:
    """Evaluates deterministic business rules against entity data."""

    @classmethod
    def evaluate_rule(
        cls, rule: dict[str, Any] | BusinessRule, entity_data: dict[str, Any]
    ) -> bool:
        """Evaluates a single rule (all conditions must pass)."""
        # If it's a dict, we extract conditions
        if isinstance(rule, dict):
            conditions = rule.get("conditions", [])
        else:
            conditions = rule.conditions

        for condition in conditions:
            # Handle both dict and Pydantic model for condition
            if hasattr(condition, "field_name"):
                field = condition.field_name
                operator = condition.operator
                value = condition.value
            else:
                field = condition.get("field_name")
                operator = condition.get("operator")
                value = condition.get("value")

            entity_val = entity_data.get(field)
            if not cls._evaluate_condition(entity_val, operator, value):
                return False

        return True

    @classmethod
    def _evaluate_condition(
        cls, entity_val: Any, operator: RuleOperator | str, reference_val: Any
    ) -> bool:
        """Evaluates a single condition."""
        op = operator.value if hasattr(operator, "value") else str(operator).upper()

        if op == "EXISTS":
            return entity_val is not None
        if entity_val is None:
            # If entity value is None but operator is not EXISTS, it fails
            return False

        try:
            if op == "EQ" or op == "=":
                return entity_val == reference_val
            elif op == "NEQ" or op == "!=":
                return entity_val != reference_val
            elif op == "GT" or op == ">":
                return float(entity_val) > float(reference_val)
            elif op == "LT" or op == "<":
                return float(entity_val) < float(reference_val)
            elif op == "GTE" or op == ">=":
                return float(entity_val) >= float(reference_val)
            elif op == "LTE" or op == "<=":
                return float(entity_val) <= float(reference_val)
            elif op == "IN":
                if not isinstance(reference_val, (list, tuple, set)):
                    return False
                return entity_val in reference_val
            elif op == "NOT_IN":
                if not isinstance(reference_val, (list, tuple, set)):
                    return False
                return entity_val not in reference_val
            else:
                return False
        except (ValueError, TypeError):
            return False
