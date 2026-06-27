"""Rule Checker Agent output schemas."""

from pydantic import BaseModel, Field


class RuleViolation(BaseModel):
    """Represents a single business rule violation."""

    rule_id: str = Field(description="The ID of the violated rule")
    rule_description: str = Field(description="Human-readable description of the rule")
    violation_detail: str = Field(description="Details on how the rule was violated")


class ValidationResult(BaseModel):
    """The final output of the Rule Checker Agent."""

    is_valid: bool = Field(
        description="Whether the recommendation passed all hard rules"
    )
    violated_rules: list[RuleViolation] = Field(
        default_factory=list, description="List of rules that were violated"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Non-blocking warnings or policy alerts"
    )
    requires_replanning: bool = Field(
        default=False,
        description="True if violations are severe enough to require replanning",
    )
    requires_human_review: bool = Field(
        default=True, description="True if the result needs manual review"
    )
