"""Application configuration — load and validate environment variables via Pydantic Settings."""

from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration object.

    All fields are loaded from environment variables (case-insensitive).
    Secrets must be provided via the environment; they are never hard-coded.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True
    app_log_level: str = "INFO"
    app_cors_origins: str | list[str] = ["http://localhost:5173"]
    secret_key: str = "change-me"

    # ── Authentication & Authorization ───────────────────────────────────────
    jwt_secret_key: str = "super-secret-jwt-key-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # ── MongoDB Atlas ────────────────────────────────────────────────────────
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "decision_intelligence"

    # ── Qdrant Cloud ─────────────────────────────────────────────────────────
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection_name: str = "knowledge_chunks"


    # ── OpenAI ───────────────────────────────────────────────────────────────
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o"

    # ── Feature Flags ────────────────────────────────────────────────────────
    enable_async_learner: bool = True

    # ── Validators ───────────────────────────────────────────────────────────
    @field_validator("app_env")
    @classmethod
    def validate_env(cls, value: str) -> str:
        allowed = {"development", "staging", "production"}
        if value not in allowed:
            raise ValueError(f"app_env must be one of {allowed}, got: {value!r}")
        return value

    @field_validator("app_log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = value.upper()
        if upper not in allowed:
            raise ValueError(f"app_log_level must be one of {allowed}")
        return upper

    @field_validator("app_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",")]
        return value  # type: ignore[return-value]

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        if (
            not value
            or value == "super-secret-jwt-key-change-me"
            or value == "change-me"
        ):
            raise ValueError("A valid JWT Secret must be provided")
        return value

    @field_validator("mongodb_uri")
    @classmethod
    def validate_mongo_uri(cls, value: str) -> str:
        if not value or not value.startswith("mongodb"):
            raise ValueError("A valid MongoDB URI must be provided")
        return value

    @field_validator("qdrant_url")
    @classmethod
    def validate_qdrant_url(cls, value: str) -> str:
        if not value or not value.startswith("http"):
            raise ValueError("A valid Qdrant URL must be provided")
        return value

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_api_key(cls, value: str) -> str:
        if not value:
            raise ValueError("OpenAI API Key must be provided")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return Settings()
