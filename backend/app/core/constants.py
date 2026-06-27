"""Platform-wide constants.

No magic strings or numbers outside of this module.
All values are read-only — never mutate at runtime.
"""

# API versioning
API_V1_PREFIX: str = "/api/v1"

# Pagination defaults
DEFAULT_PAGE_SIZE: int = 20
MAX_PAGE_SIZE: int = 100

# Logging event names (use dotted namespacing: component.action)
LOG_APP_STARTUP: str = "application.startup"
LOG_APP_SHUTDOWN: str = "application.shutdown"
