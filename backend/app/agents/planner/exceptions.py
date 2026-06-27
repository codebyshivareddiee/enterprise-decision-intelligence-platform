"""Exceptions for the Planner Agent."""

class PlannerError(Exception):
    """Base exception for all Planner-related errors."""
    pass


class PlanGenerationError(PlannerError):
    """Raised when the Planner fails to generate a valid ExecutionPlan."""
    pass
