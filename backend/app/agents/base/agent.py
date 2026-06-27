"""Base agent interface that all specialized agents must implement."""

from abc import ABC, abstractmethod

from app.agents.base.exceptions import MissingArtifactError
from app.workflow.models import WorkflowState


class BaseAgent(ABC):
    """The common interface for all execution agents."""

    @property
    @abstractmethod
    def consumes(self) -> list[str]:
        """List of artifacts this agent expects to exist in the WorkflowState."""
        ...

    @property
    @abstractmethod
    def produces(self) -> list[str]:
        """List of artifacts this agent produces and writes to the WorkflowState."""
        ...

    def validate_inputs(self, state: WorkflowState) -> None:
        """Validate that all declared inputs exist in the state."""
        for artifact in self.consumes:
            value = getattr(state, artifact, None)
            if value is None:
                raise MissingArtifactError(
                    f"Agent requires artifact '{artifact}' but it was not found in WorkflowState."
                )

    @abstractmethod
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute the agent's logic.

        Args:
            state: The current WorkflowState containing context and prior artifacts.

        Returns:
            WorkflowState: The updated state with the new artifact.

        Raises:
            MissingArtifactError: If required input artifacts are missing.
        """
        ...
