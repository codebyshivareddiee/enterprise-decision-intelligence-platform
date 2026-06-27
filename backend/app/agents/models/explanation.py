"""Explanation Agent output schemas."""

from pydantic import BaseModel, Field


class CitedChunk(BaseModel):
    """A knowledge chunk cited in the explanation."""

    text: str = Field(description="The text content of the cited chunk")
    asset_id: str = Field(description="The ID of the source knowledge asset")


class ExplanationResult(BaseModel):
    """The final output of the Explanation Agent."""

    summary: str = Field(
        description="A plain-language summary of why the recommendation was made"
    )
    evidence_references: list[str] = Field(
        default_factory=list,
        description="References to evidence supporting the recommendation",
    )
    applied_rules: list[str] = Field(
        default_factory=list, description="Business rules that influenced the decision"
    )
    confidence_reasoning: str = Field(
        description="Explanation of the confidence level assigned to the recommendation"
    )
    cited_chunks: list[CitedChunk] = Field(
        default_factory=list,
        description="Specific knowledge chunks cited in the explanation",
    )
