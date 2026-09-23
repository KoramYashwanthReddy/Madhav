"""Integration tests for Module 05 Model Management API endpoints."""

import pytest
from fastapi.testclient import TestClient

from max.main import app


@pytest.fixture
def client() -> TestClient:
    """Return TestClient instance for Max API."""
    return TestClient(app)


class TestModelManagementAPI:
    """Integration tests for Model Management endpoints."""

    def test_list_models(self, client: TestClient) -> None:
        response = client.get("/api/v1/models")
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        data = json_data["data"]
        assert "models" in data
        assert data["total"] >= 1
        assert any(m["model_id"] == "development-stub" for m in data["models"])

    def test_get_model_details(self, client: TestClient) -> None:
        response = client.get("/api/v1/models/development-stub")
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        data = json_data["data"]
        assert data["model_id"] == "development-stub"
        assert data["provider"] == "development"

    def test_register_new_model(self, client: TestClient) -> None:
        payload = {
            "model_id": "api-test-model-1",
            "provider": "local",
            "name": "API Test Model 1",
            "version": "1.0.0",
            "description": "Integration test model definition",
        }
        response = client.post("/api/v1/models", json=payload)
        assert response.status_code == 201
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["model_id"] == "api-test-model-1"

    def test_update_model(self, client: TestClient) -> None:
        payload = {"description": "Updated model description text."}
        response = client.patch("/api/v1/models/development-stub", json=payload)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["description"] == "Updated model description text."

    def test_load_and_unload_model(self, client: TestClient) -> None:
        load_res = client.post("/api/v1/models/development-stub/load")
        assert load_res.status_code == 200
        assert load_res.json()["data"]["lifecycle_state"] == "loaded"

        status_res = client.get("/api/v1/models/development-stub/status")
        assert status_res.status_code == 200
        assert status_res.json()["data"]["is_loaded"] is True

        unload_res = client.post("/api/v1/models/development-stub/unload")
        assert unload_res.status_code == 200
        assert unload_res.json()["data"]["lifecycle_state"] == "available"

    def test_get_model_capabilities(self, client: TestClient) -> None:
        response = client.get("/api/v1/models/development-stub/capabilities")
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["success"] is True
        assert json_data["data"]["text_generation"] is True

    def test_get_nonexistent_model_returns_404(self, client: TestClient) -> None:
        response = client.get("/api/v1/models/nonexistent-model-id")
        assert response.status_code == 404
        json_data = response.json()
        assert json_data["success"] is False
        assert json_data["error"]["code"] == "MODEL_NOT_FOUND"

    def test_delete_model_registration(self, client: TestClient) -> None:
        reg_payload = {
            "model_id": "temp-model-to-delete",
            "provider": "local",
            "name": "Temp Model",
        }
        client.post("/api/v1/models", json=reg_payload)

        del_res = client.delete("/api/v1/models/temp-model-to-delete")
        assert del_res.status_code == 200
        assert del_res.json()["data"]["deleted"] is True

        get_res = client.get("/api/v1/models/temp-model-to-delete")
        assert get_res.status_code == 404
