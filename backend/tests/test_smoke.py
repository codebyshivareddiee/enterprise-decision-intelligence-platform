"""Smoke tests — verify the application starts and core routes respond."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    """Return a synchronous TestClient for the FastAPI app."""
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    """GET /api/v1/health returns 200 with status=ok."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_readiness_probe(client: TestClient) -> None:
    """GET /api/v1/ready returns 200 with status=ready."""
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
