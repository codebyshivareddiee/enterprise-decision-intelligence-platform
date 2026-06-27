"""Exceptions for specialized agents."""


class AgentError(Exception):
    """Base exception for all agent-related errors."""

    pass


class MissingArtifactError(AgentError):
    """Raised when an agent requires an artifact that is not present in the state."""

    pass
