"""Abstract base class for LLM providers."""

import abc
from typing import Any

from pydantic import BaseModel


class LLMProvider(abc.ABC):
    """Interface that all LLM providers must implement."""

    @abc.abstractmethod
    async def generate(
        self,
        prompt: str,
        response_schema: type[BaseModel] | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.2,
    ) -> str | BaseModel:
        """Generate text or structured data from a prompt."""
        pass

    @abc.abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        pass

    @abc.abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Verify provider connectivity, configured model, and API availability.

        Returns a dictionary with at least {"status": "ok" | "error", "provider": "..."}
        """
        pass
