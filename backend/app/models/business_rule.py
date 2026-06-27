"""BusinessRule domain model.

Business rules are deterministic filter conditions evaluated before AI
reasoning. Hard-failing rules always exclude candidates — GPT-5 can
never override them (see DO_NOT_CHANGE.md).

Rules are stored as structured configuration, never as executable code.
"""

from uuid import UUID

from pydantic import BaseModel, Field

from app.models.base import AuditedModel
from app.models.enums import RuleOperator, RuleType


class RuleCondition(BaseModel):
    """A single condition expression within a business rule.

    Represents: ``field_name operator value``

    Example:
        - ``years_experience`` ``gte`` ``5``
        - ``location`` ``in`` ``["New York", "Remote"]``

    Attributes:
        field_name: The schema field this condition evaluates against.
            Must match a ``SchemaField.name`` in the workspace schema.
        operator: Comparison operator to apply.
        value: The reference value for the comparison. Type depends on
            ``operator``: scalar for most operators, list for ``IN``
            and ``NOT_IN``, ``None`` for ``EXISTS``.
    """

    field_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Schema field name this condition targets.",
    )
    operator: RuleOperator = Field(
        ...,
        description="Comparison operator to apply.",
    )
    value: object = Field(
        default=None,
        description=(
            "Reference value for the comparison. Scalar, list, or None depending "
            "on the operator."
        ),
    )


class BusinessRule(AuditedModel):
    """A deterministic evaluation rule applied before AI reasoning.

    Business rules are never delegated to AI. A ``HARD_FILTER`` rule
    that fails unconditionally excludes the candidate — GPT-5 cannot
    override it (architectural invariant from DO_NOT_CHANGE.md).

    Attributes:
        organization_id: Owning organization — tenant isolation.
        workspace_id: Workspace this rule applies to.
        name: Human-readable rule name (e.g. ``"Minimum 5 Years
            Experience"``).
        description: Optional explanation of the rule's intent and
            business rationale.
        rule_type: Classification that determines how this rule
            influences the workflow.
        conditions: One or more conditions that together constitute the
            rule. All conditions are AND-ed unless otherwise specified
            by future extensions.
        is_active: Whether this rule is currently enforced. Inactive
            rules are stored but not evaluated.
        weight: Numeric weight (0.0–1.0) used only for
            ``SOFT_PREFERENCE`` rules to influence ranking. Ignored for
            ``HARD_FILTER`` and ``MANDATORY_FIELD`` rules.
        priority: Evaluation order within the workspace. Lower numbers
            are evaluated first.
    """

    organization_id: UUID = Field(
        ...,
        description="ID of the owning Organization.",
    )
    workspace_id: UUID = Field(
        ...,
        description="ID of the Workspace this rule belongs to.",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable rule name.",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional explanation of the rule's business rationale.",
    )
    rule_type: RuleType = Field(
        ...,
        description="Classification determining how this rule affects workflow execution.",
    )
    conditions: list[RuleCondition] = Field(
        default_factory=list,
        min_length=1,
        description="One or more conditions that constitute this rule (AND-ed together).",
    )
    is_active: bool = Field(
        default=True,
        description="Whether this rule is currently enforced during evaluation.",
    )
    weight: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description=(
            "Influence weight (0.0–1.0) for SOFT_PREFERENCE rules only. "
            "Ignored for HARD_FILTER and MANDATORY_FIELD rules."
        ),
    )
    priority: int = Field(
        default=100,
        ge=1,
        description="Evaluation order. Lower numbers are evaluated first.",
    )
