"""Tests for application settings loading."""

import pytest

from app.config.settings import Settings


def test_settings_defaults() -> None:
    """Settings can be instantiated with defaults and no .env file."""
    s = Settings(
        _env_file=None,  # type: ignore[call-arg]
        secret_key="test-secret",
    )
    assert s.app_env == "development"
    assert s.app_port == 8000
    assert s.app_log_level == "INFO"


def test_settings_validates_env() -> None:
    """Invalid app_env raises a validation error."""
    with pytest.raises(Exception):
        Settings(
            _env_file=None,  # type: ignore[call-arg]
            app_env="invalid",
            secret_key="test-secret",
        )


def test_settings_log_level_uppercase() -> None:
    """Log level is normalised to uppercase."""
    s = Settings(
        _env_file=None,  # type: ignore[call-arg]
        app_log_level="debug",
        secret_key="test-secret",
    )
    assert s.app_log_level == "DEBUG"
