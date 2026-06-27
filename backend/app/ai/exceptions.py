"""Custom exceptions for the AI Layer."""

class ProviderError(Exception):
    """Raised when the underlying LLM provider encounters an error."""
    pass

class InvalidResponseError(Exception):
    """Raised when the LLM response cannot be parsed or does not match the expected schema."""
    pass

class EmbeddingError(Exception):
    """Raised when there is an error generating embeddings."""
    pass

class RateLimitError(ProviderError):
    """Raised when the LLM provider's rate limit is exceeded."""
    pass
