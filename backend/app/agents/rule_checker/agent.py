"""Rule Checker Agent implementation."""

from app.agents.base.agent import BaseAgent
from app.agents.models.validation import RuleViolation, ValidationResult
from app.agents.rule_checker.engine import RuleEngine
from app.workflow.models import WorkflowState


class RuleCheckerAgent(BaseAgent):
    """Validates the recommendation against deterministic business rules."""

    @property
    def consumes(self) -> list[str]:
        return ["recommendation", "business_rules", "retrieved_chunks"]

    @property
    def produces(self) -> list[str]:
        return ["validation_result"]

    async def execute(self, state: WorkflowState) -> WorkflowState:
        self.validate_inputs(state)

        # We need entity data to evaluate.
        # Retrieve entity data from retrieved_chunks metadata based on recommendation.entity_id
        if not state.recommendation:
            raise ValueError("Recommendation result missing in state")
        recommended_entity_id = state.recommendation.recommendation.entity_id
        entity_data = {}

        if state.retrieved_chunks:
            for chunk in state.retrieved_chunks.chunks:
                if (
                    chunk.asset_id == recommended_entity_id
                    or str(chunk.metadata.get("id")) == recommended_entity_id
                ):
                    entity_data.update(chunk.metadata)

        violated_rules = []
        warnings = []

        if state.business_rules:
            for rule in state.business_rules:
                # evaluate_rule returns True if passes, False if fails
                passes = RuleEngine.evaluate_rule(rule, entity_data)
                if not passes:
                    rule_type = rule.get("rule_type")
                    rule_type_str = str(rule_type).upper() if rule_type else ""

                    if "HARD_FILTER" in rule_type_str or "MANDATORY" in rule_type_str:
                        violated_rules.append(
                            RuleViolation(
                                rule_id=str(rule.get("id", "")),
                                rule_description=rule.get("name", ""),
                                violation_detail=f"Entity failed hard constraint: {rule.get('description', '')}",
                            )
                        )
                    else:
                        warnings.append(
                            f"Entity failed soft preference: {rule.get('name', '')}"
                        )

        is_valid = len(violated_rules) == 0
        requires_replanning = not is_valid

        result = ValidationResult(
            is_valid=is_valid,
            violated_rules=violated_rules,
            warnings=warnings,
            requires_replanning=requires_replanning,
            requires_human_review=True,  # Always require review before final action
        )

        state.validation_result = result
        return state
