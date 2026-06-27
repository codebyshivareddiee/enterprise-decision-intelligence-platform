"""Learner Agent output schemas."""

from typing import Any

from pydantic import BaseModel, Field


class PreferenceUpdateResult(BaseModel):
    """The final output of the Learner Agent representing preference changes."""

    workspace_id: str = Field(
        description="The workspace this preference update applies to"
    )
    learned_attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Attributes and their learned weights or preferences",
    )
    learning_signal: str = Field(
        description="A summary of what was learned from the human decision"
    )
