"""Unit tests for root, health, and readiness endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient) -> None:
    """Test GET / endpoint returns correct identity structure."""
    response = await client.get("/")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["name"] == "MAX"
    assert json_data["data"]["service"] == "max"
    assert json_data["data"]["version"] == "0.1.0"
    assert json_data["data"]["message"] == "MAX platform is running."
    assert "request_id" in json_data
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient) -> None:
    """Test GET /health liveness probe."""
    response = await client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "ok"
    assert json_data["data"]["service"] == "max"
    assert json_data["data"]["version"] == "0.1.0"
    assert "request_id" in json_data
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_readiness_endpoint(client: AsyncClient) -> None:
    """Test GET /ready readiness probe."""
    response = await client.get("/ready")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "ready"
    assert json_data["data"]["service"] == "max"
    assert json_data["data"]["version"] == "0.1.0"
    assert "request_id" in json_data
    assert "X-Request-ID" in response.headers
