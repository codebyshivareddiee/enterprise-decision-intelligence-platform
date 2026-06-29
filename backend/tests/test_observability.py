"""P13 Observability & Monitoring — Unit Tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

# ── helpers ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def client() -> TestClient:
    from app.main import app

    return TestClient(app)


# ── 1. Metrics registry exports all required metric names ────────────────────


def test_metrics_registry_api() -> None:
    """API metrics are registered."""
    from app.core.metrics import REQUEST_DURATION, REQUESTS_TOTAL

    assert REQUESTS_TOTAL._name == "api_requests"
    assert REQUEST_DURATION._name == "api_request_duration_seconds"


def test_metrics_registry_llm() -> None:
    """LLM metrics are registered."""
    from app.core.metrics import LLM_LATENCY, LLM_REQUESTS_TOTAL, LLM_TOKENS

    assert LLM_REQUESTS_TOTAL._name == "llm_requests"
    assert LLM_LATENCY._name == "llm_latency_seconds"
    assert LLM_TOKENS._name == "llm_tokens"


def test_metrics_registry_workflow() -> None:
    """Workflow metrics are registered."""
    from app.core.metrics import (
        AGENT_ARTIFACTS,
        AGENT_DURATION,
        AGENT_EXECUTIONS_TOTAL,
        WORKFLOW_DURATION,
        WORKFLOWS_TOTAL,
    )

    assert WORKFLOWS_TOTAL._name == "workflows"
    assert WORKFLOW_DURATION._name == "workflow_duration_seconds"
    assert AGENT_EXECUTIONS_TOTAL._name == "agent_executions"
    assert AGENT_DURATION._name == "agent_duration_seconds"
    assert AGENT_ARTIFACTS._name == "agent_artifacts"


def test_metrics_registry_knowledge() -> None:
    """Knowledge layer metrics are registered."""
    from app.core.metrics import (
        AI_OVERRIDE_DECISIONS,
        DOCUMENTS_PROCESSED_TOTAL,
        DUPLICATE_DOCUMENTS_TOTAL,
        KNOWLEDGE_DEFAULTS_USED,
        RULE_BASED_DECISIONS,
    )

    assert DOCUMENTS_PROCESSED_TOTAL._name == "documents_processed"
    assert DUPLICATE_DOCUMENTS_TOTAL._name == "duplicate_documents"
    assert KNOWLEDGE_DEFAULTS_USED._name == "schema_defaults_used"
    assert RULE_BASED_DECISIONS._name == "rule_based_decisions"
    assert AI_OVERRIDE_DECISIONS._name == "ai_override_decisions"


def test_metrics_registry_workspace() -> None:
    """Workspace metrics are Gauges (not Counters)."""
    from prometheus_client import Gauge

    from app.core.metrics import WORKSPACE_ASSETS, WORKSPACE_SCHEMAS

    assert isinstance(WORKSPACE_ASSETS, Gauge)
    assert isinstance(WORKSPACE_SCHEMAS, Gauge)
    assert WORKSPACE_ASSETS._name == "workspace_assets_current"
    assert WORKSPACE_SCHEMAS._name == "workspace_schemas_current"


# ── 2. /live endpoint ─────────────────────────────────────────────────────────


def test_live_endpoint(client: TestClient) -> None:
    """GET /api/v1/live returns 200 ok."""
    resp = client.get("/api/v1/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── 3. /metrics endpoint returns Prometheus text ─────────────────────────────


def test_metrics_endpoint(client: TestClient) -> None:
    """GET /api/v1/metrics returns Prometheus text exposition format."""
    resp = client.get("/api/v1/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    body = resp.text
    assert "api_requests_total" in body
    assert "llm_requests_total" in body
    assert "workflows_total" in body
    assert "documents_processed_total" in body
    assert "workspace_assets_current" in body


# ── 4. /health endpoint ───────────────────────────────────────────────────────


def test_health_endpoint(client: TestClient) -> None:
    """GET /api/v1/health returns 200 with status=ok."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body


# ── 5. openai_provider: empty choices raises InvalidResponseError ─────────────


@pytest.mark.asyncio
async def test_openai_provider_empty_choices_raises() -> None:
    """_execute_generate raises InvalidResponseError when choices is empty."""
    import unittest.mock as mock

    from app.ai.exceptions import InvalidResponseError
    from app.ai.providers.openai_provider import OpenAIProvider

    provider = OpenAIProvider.__new__(OpenAIProvider)
    provider.chat_model = "gpt-4o"

    fake_completion = mock.MagicMock()
    fake_completion.choices = []

    mock_client = mock.AsyncMock()
    mock_client.chat.completions.create = mock.AsyncMock(return_value=fake_completion)
    provider.client = mock_client

    with pytest.raises(InvalidResponseError, match="empty choices"):
        await provider._execute_generate(
            messages=[{"role": "user", "content": "test"}],
            temperature=0.2,
            response_schema=None,
        )


# ── 6. openai_provider: refusal raises InvalidResponseError ──────────────────


@pytest.mark.asyncio
async def test_openai_provider_refusal_raises() -> None:
    """_execute_generate raises InvalidResponseError on model refusal."""
    import unittest.mock as mock

    from app.ai.exceptions import InvalidResponseError
    from app.ai.providers.openai_provider import OpenAIProvider

    provider = OpenAIProvider.__new__(OpenAIProvider)
    provider.chat_model = "gpt-4o"

    fake_message = mock.MagicMock()
    fake_message.refusal = "I cannot help with that."
    fake_message.content = None

    fake_choice = mock.MagicMock()
    fake_choice.message = fake_message

    fake_completion = mock.MagicMock()
    fake_completion.choices = [fake_choice]
    fake_completion.usage = None

    mock_client = mock.AsyncMock()
    mock_client.chat.completions.create = mock.AsyncMock(return_value=fake_completion)
    provider.client = mock_client

    with pytest.raises(InvalidResponseError, match="refused"):
        await provider._execute_generate(
            messages=[{"role": "user", "content": "test"}],
            temperature=0.2,
            response_schema=None,
        )


# ── 7. openai_provider: successful path emits metrics ─────────────────────────


@pytest.mark.asyncio
async def test_openai_provider_success_increments_metrics() -> None:
    """Successful _execute_generate increments LLM_REQUESTS_TOTAL counter."""
    import unittest.mock as mock

    from app.ai.providers.openai_provider import OpenAIProvider
    from app.core.metrics import LLM_REQUESTS_TOTAL

    provider = OpenAIProvider.__new__(OpenAIProvider)
    provider.chat_model = "gpt-4o"

    fake_usage = mock.MagicMock()
    fake_usage.prompt_tokens = 10
    fake_usage.completion_tokens = 20
    fake_usage.total_tokens = 30

    fake_message = mock.MagicMock()
    fake_message.refusal = None
    fake_message.content = "Hello"

    fake_choice = mock.MagicMock()
    fake_choice.message = fake_message

    fake_completion = mock.MagicMock()
    fake_completion.choices = [fake_choice]
    fake_completion.usage = fake_usage

    mock_client = mock.AsyncMock()
    mock_client.chat.completions.create = mock.AsyncMock(return_value=fake_completion)
    provider.client = mock_client

    before = LLM_REQUESTS_TOTAL.labels(
        provider="openai", model="gpt-4o", operation="generate", status="success"
    )._value.get()

    result = await provider._execute_generate(
        messages=[{"role": "user", "content": "test"}],
        temperature=0.2,
        response_schema=None,
    )

    after = LLM_REQUESTS_TOTAL.labels(
        provider="openai", model="gpt-4o", operation="generate", status="success"
    )._value.get()

    assert result == "Hello"
    assert after == before + 1
