"""Facade for the AI Layer."""

from typing import Any

from pydantic import BaseModel

from app.ai.providers.base import LLMProvider
from app.ai.providers.openai_provider import OpenAIProvider


class AIManager:
    """The central entry point for all AI capabilities in the platform.

    This facade abstracts away the underlying provider implementation and
    exposes a small, focused API.
    """

    def __init__(self, provider: LLMProvider | None = None) -> None:
        # Default to OpenAIProvider if none provided
        self._provider = provider or OpenAIProvider()

    async def generate(
        self,
        prompt: str,
        response_schema: type[BaseModel] | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.2,
    ) -> str | BaseModel:
        """Generate a response from the LLM.

        If `response_schema` is provided, the LLM will return a parsed Pydantic object.
        Otherwise, it returns a plain text string.
        """
        return await self._provider.generate(
            prompt=prompt,
            response_schema=response_schema,
            system_prompt=system_prompt,
            temperature=temperature,
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        return await self._provider.embed(texts)

    async def health_check(self) -> dict[str, Any]:
        """Verify the health and configuration of the underlying LLM provider."""
        return await self._provider.health_check()
