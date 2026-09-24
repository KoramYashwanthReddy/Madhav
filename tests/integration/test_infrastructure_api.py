"""Integration tests for Module 38 — Infrastructure & Production Deployment API routes."""

import pytest
from fastapi.testclient import TestClient

from max.core.application import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_get_infrastructure_status(client: TestClient) -> None:
    response = client.get("/api/v1/infrastructure/status")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "version" in data["data"]
    assert "services" in data["data"]
    assert "gpu" in data["data"]
    assert "resources" in data["data"]


def test_get_infrastructure_metrics(client: TestClient) -> None:
    response = client.get("/api/v1/infrastructure/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "cpu_usage_percent" in data["data"]
    assert "memory_used_mb" in data["data"]


def test_get_gpu_status(client: TestClient) -> None:
    response = client.get("/api/v1/infrastructure/gpu")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "available" in data["data"]


def test_get_secret_rotation_status(client: TestClient) -> None:
    response = client.get("/api/v1/infrastructure/secrets/rotation")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0


def test_get_presigned_url(client: TestClient) -> None:
    response = client.get("/api/v1/infrastructure/storage/presigned-url?object_name=test.txt")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "presigned_url" in data["data"]
    assert "test.txt" in data["data"]["presigned_url"]
