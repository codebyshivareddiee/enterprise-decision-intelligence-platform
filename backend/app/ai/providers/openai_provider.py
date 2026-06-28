"""OpenAI provider implementation."""

import time
import uuid
from typing import Any, cast

import openai
import structlog
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.ai.exceptions import (
    EmbeddingError,
    InvalidResponseError,
    ProviderError,
    RateLimitError,
)
from app.ai.providers.base import LLMProvider
from app.config.settings import get_settings

logger = structlog.get_logger(__name__)


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.chat_model = settings.openai_chat_model
        self.embedding_model = settings.openai_embedding_model
        self.client = AsyncOpenAI(api_key=self.api_key)

    def _map_exception(self, e: Exception) -> Exception:
        if isinstance(e, openai.RateLimitError):
            return RateLimitError(str(e))
        if isinstance(e, (openai.APIError, openai.APIConnectionError)):
            return ProviderError(str(e))
        if isinstance(e, openai.LengthFinishReasonError):
            return InvalidResponseError(
                "Response was truncated due to max_tokens limit"
            )
        return e

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(
            (
                openai.RateLimitError,
                openai.APIConnectionError,
                openai.InternalServerError,
            )
        ),
        reraise=True,
    )
    async def _execute_generate(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        response_schema: type[BaseModel] | None,
    ) -> Any:
        start_time = time.time()
        req_id = str(uuid.uuid4())

        log_ctx = {
            "request_id": req_id,
            "model": self.chat_model,
        }
        logger.info("llm_generate_start", **log_ctx)

        try:
            kwargs: dict[str, Any] = {
                "model": self.chat_model,
                "messages": messages,
                "temperature": temperature,
            }

            if response_schema:
                # Use standard Responses API with json_schema
                kwargs["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": response_schema.__name__,
                        "schema": response_schema.model_json_schema(),
                    },
                }

            completion: ChatCompletion = cast(
                ChatCompletion,
                await self.client.chat.completions.create(**kwargs),
            )

            if not completion.choices:
                raise InvalidResponseError("Model returned an empty choices list.")

            message = completion.choices[0].message

            refusal = getattr(message, "refusal", None)
            if refusal:
                raise InvalidResponseError(
                    f"Model refused to generate output: {refusal}"
                )

            content: str = message.content or ""
            elapsed = time.time() - start_time

            usage = completion.usage
            prompt_tokens: int = usage.prompt_tokens if usage else 0
            completion_tokens: int = usage.completion_tokens if usage else 0
            total_tokens: int = usage.total_tokens if usage else 0

            from app.core.metrics import LLM_LATENCY, LLM_REQUESTS_TOTAL, LLM_TOKENS

            LLM_REQUESTS_TOTAL.labels(
                provider="openai",
                model=self.chat_model,
                operation="generate",
                status="success",
            ).inc()
            LLM_LATENCY.labels(
                provider="openai", model=self.chat_model, operation="generate"
            ).observe(elapsed)
            LLM_TOKENS.labels(
                provider="openai", model=self.chat_model, token_type="prompt"
            ).inc(prompt_tokens)
            LLM_TOKENS.labels(
                provider="openai", model=self.chat_model, token_type="completion"
            ).inc(completion_tokens)

            logger.info(
                "llm_generate_success",
                execution_time_s=round(elapsed, 3),
                latency_ms=round(elapsed * 1000, 2),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                success=True,
                **log_ctx,
            )

            if response_schema:
                try:
                    return response_schema.model_validate_json(content)
                except Exception as e:
                    raise InvalidResponseError(
                        f"Failed to parse model output into schema: {e}"
                    ) from e

            return content

        except InvalidResponseError:
            # Already a clean domain error (refusal, schema parse failure).
            # Propagate as-is — do NOT re-map or double-count in metrics.
            raise
        except Exception as e:
            elapsed = time.time() - start_time
            from app.core.metrics import LLM_REQUESTS_TOTAL

            LLM_REQUESTS_TOTAL.labels(
                provider="openai",
                model=self.chat_model,
                operation="generate",
                status="error",
            ).inc()
            logger.error(
                "llm_generate_error",
                execution_time_s=round(elapsed, 3),
                latency_ms=round(elapsed * 1000, 2),
                error=str(e),
                success=False,
                failure_reason=str(e),
                **log_ctx,
            )
            raise self._map_exception(e) from None

    async def generate(
        self,
        prompt: str,
        response_schema: type[BaseModel] | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.2,
    ) -> str | BaseModel:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return await self._execute_generate(messages, temperature, response_schema)

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(
            (
                openai.RateLimitError,
                openai.APIConnectionError,
                openai.InternalServerError,
            )
        ),
        reraise=True,
    )
    async def _execute_embed(self, texts: list[str]) -> list[list[float]]:
        start_time = time.time()
        req_id = str(uuid.uuid4())

        log_ctx = {
            "request_id": req_id,
            "model": self.embedding_model,
            "num_texts": len(texts),
        }
        logger.info("llm_embed_start", **log_ctx)

        try:
            response = await self.client.embeddings.create(
                input=texts, model=self.embedding_model
            )

            embeddings = [
                item.embedding for item in sorted(response.data, key=lambda x: x.index)
            ]
            elapsed = time.time() - start_time

            prompt_tokens = response.usage.prompt_tokens if response.usage else 0
            total_tokens = response.usage.total_tokens if response.usage else 0

            from app.core.metrics import LLM_LATENCY, LLM_REQUESTS_TOTAL, LLM_TOKENS

            LLM_REQUESTS_TOTAL.labels(
                provider="openai",
                model=self.embedding_model,
                operation="embed",
                status="success",
            ).inc()
            LLM_LATENCY.labels(
                provider="openai", model=self.embedding_model, operation="embed"
            ).observe(elapsed)
            LLM_TOKENS.labels(
                provider="openai", model=self.embedding_model, token_type="prompt"
            ).inc(prompt_tokens)

            logger.info(
                "llm_embed_success",
                execution_time_s=round(elapsed, 3),
                latency_ms=round(elapsed * 1000, 2),
                prompt_tokens=prompt_tokens,
                completion_tokens=0,
                total_tokens=total_tokens,
                success=True,
                **log_ctx,
            )
            return embeddings

        except Exception as e:
            elapsed = time.time() - start_time
            from app.core.metrics import LLM_REQUESTS_TOTAL

            LLM_REQUESTS_TOTAL.labels(
                provider="openai",
                model=self.embedding_model,
                operation="embed",
                status="error",
            ).inc()
            logger.error(
                "llm_embed_error",
                execution_time_s=round(elapsed, 3),
                latency_ms=round(elapsed * 1000, 2),
                error=str(e),
                success=False,
                failure_reason=str(e),
                **log_ctx,
            )
            raise EmbeddingError(str(self._map_exception(e))) from None

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await self._execute_embed(texts)

    async def health_check(self) -> dict[str, Any]:
        """Verify provider connectivity."""
        status = {
            "provider": "openai",
            "chat_model": self.chat_model,
            "embedding_model": self.embedding_model,
            "status": "ok",
        }
        try:
            await self.client.models.list()
        except Exception as e:
            status["status"] = "error"
            status["error"] = str(e)

        return status
