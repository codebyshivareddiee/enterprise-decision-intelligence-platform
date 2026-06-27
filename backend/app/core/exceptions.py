"""Core exception hierarchy for the platform.

All domain-specific exceptions extend PlatformError so callers can catch
broad or narrow exceptions as needed.
"""


class PlatformError(Exception):
    """Base exception for all platform errors."""

    def __init__(self, message: str, code: str = "PLATFORM_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class NotFoundError(PlatformError):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            message=f"{resource} not found: {identifier}",
            code="NOT_FOUND",
        )
        self.resource = resource
        self.identifier = identifier


class ValidationError(PlatformError):
    """Raised when input data fails domain validation."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="VALIDATION_ERROR")


class AuthorizationError(PlatformError):
    """Raised when an operation is not permitted for the caller."""

    def __init__(self, message: str = "Access denied.") -> None:
        super().__init__(message=message, code="AUTHORIZATION_ERROR")


class ConfigurationError(PlatformError):
    """Raised when the application is misconfigured."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="CONFIGURATION_ERROR")


class ExternalServiceError(PlatformError):
    """Raised when an external service call fails."""

    def __init__(self, service: str, message: str) -> None:
        super().__init__(
            message=f"External service error [{service}]: {message}",
            code="EXTERNAL_SERVICE_ERROR",
        )
        self.service = service
