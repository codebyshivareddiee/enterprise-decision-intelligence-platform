"""Exceptions for the workflow runtime."""


class WorkflowError(Exception):
    """Base exception for workflow runtime."""

    pass


class WorkflowExecutionError(WorkflowError):
    """Raised when the workflow encounters an unrecoverable execution error."""

    pass


class MissingArtifactError(WorkflowError):
    """Raised when a required artifact is missing from the state."""

    pass


class AgentNotRegisteredError(WorkflowError):
    """Raised when an ExecutionPlan requests an agent that is not in the registry."""

    pass


class StateValidationError(WorkflowError):
    """Raised when the workflow state is invalid or fails schema validation."""

    pass


class PlannerExecutionError(WorkflowError):
    """Raised when the planner fails during a replanning operation."""

    pass
