"""Integration tests for Module 04 AI Runtime API endpoints."""

import pytest
from fastapi.testclient import TestClient

from madhav.main import app


@pytest.fixture
def client() -> TestClient:
    """Return a TestClient instance for Madhav API."""
    return TestClient(app)


class TestAIRuntimeEndpoints:
    """Integration tests for AI Runtime endpoints."""

    def test_get_runtime_status(self, client: TestClient) -> None:
        response = client.get("/api/v1/ai/runtime/status")
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["status"] == "available"
        assert json_data["data"]["provider"] == "stub"

    def test_get_runtime_capabilities(self, client: TestClient) -> None:
        response = client.get("/api/v1/ai/runtime/capabilities")
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["generation"] is True
        assert json_data["data"]["streaming"] is True

    def test_post_ai_generate_success(self, client: TestClient) -> None:
        payload = {
            "messages": [
                {"role": "system", "content": "You are Madhav AI."},
                {"role": "user", "content": "Hello Madhav"},
            ],
            "generation": {
                "temperature": 0.7,
                "max_tokens": 100,
            },
        }
        response = client.post("/api/v1/ai/generate", json=payload)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        data = json_data["data"]
        assert "content" in data
        assert "Development AI runtime response" in data["content"]
        assert data["finish_reason"] == "stop"
        assert data["provider"] == "stub"
        assert data["model_reference"] == "stub-development-model"
        assert "execution" in data
        assert data["execution"]["success"] is True

    def test_post_ai_generate_invalid_role(self, client: TestClient) -> None:
        payload = {
            "messages": [
                {"role": "invalid_role", "content": "Hello"},
            ]
        }
        response = client.post("/api/v1/ai/generate", json=payload)
        assert response.status_code == 400

    def test_post_ai_generate_empty_messages(self, client: TestClient) -> None:
        payload = {"messages": []}
        response = client.post("/api/v1/ai/generate", json=payload)
        assert response.status_code == 400

    def test_post_ai_generate_invalid_temperature(self, client: TestClient) -> None:
        payload = {
            "messages": [
                {"role": "user", "content": "Hello"},
            ],
            "generation": {
                "temperature": 5.0,  # Invalid (>2.0)
            },
        }
        response = client.post("/api/v1/ai/generate", json=payload)
        assert response.status_code == 422 or response.status_code == 400
