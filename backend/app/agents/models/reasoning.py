"""Reasoning Agent output schemas."""

from pydantic import BaseModel, Field


class EntityEvaluation(BaseModel):
    """Reasoning score and notes for a specific entity."""

    entity_id: str = Field(description="The ID of the entity being evaluated")
    ai_score: float = Field(description="AI evaluation score for this entity")
    reasoning_notes: str = Field(
        description="Detailed notes on why this score was given"
    )


class ReasoningResult(BaseModel):
    """The final output of the Reasoning Agent."""

    entity_evaluations: list[EntityEvaluation] = Field(
        default_factory=list, description="List of evaluated entities"
    )
    missing_information: list[str] = Field(
        default_factory=list, description="Missing context needed for a better decision"
    )
    identified_risks: list[str] = Field(
        default_factory=list, description="Risks identified during reasoning"
    )
    identified_opportunities: list[str] = Field(
        default_factory=list, description="Opportunities identified during reasoning"
    )
