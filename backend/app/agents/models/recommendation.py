"""Recommendation Agent output schemas."""

from pydantic import BaseModel, Field


class RecommendationItem(BaseModel):
    """A single recommended option."""

    entity_id: str = Field(description="The ID of the recommended entity")
    rank: int = Field(description="The rank of this recommendation (1 is highest)")
    final_score: float = Field(description="The final aggregated score")
    contributing_factors: list[str] = Field(
        default_factory=list, description="Factors contributing to this score"
    )


class RecommendationResult(BaseModel):
    """The final output of the Recommendation Agent."""

    recommendation: RecommendationItem = Field(
        description="The primary recommended action or entity"
    )
    confidence: float = Field(
        description="Overall confidence in this recommendation (0.0 to 1.0)"
    )
    alternatives: list[RecommendationItem] = Field(
        default_factory=list, description="Alternative recommendations"
    )
    risk_level: str = Field(
        description="Risk level of this recommendation (e.g., LOW, MEDIUM, HIGH)"
    )
