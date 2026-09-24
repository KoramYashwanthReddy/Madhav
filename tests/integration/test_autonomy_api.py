"""Integration tests for Module 41 Autonomy REST API endpoints."""

import pytest
from fastapi.testclient import TestClient

from max.core.application import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_get_autonomy_status_api(client: TestClient) -> None:
    resp = client.get("/api/v1/autonomy/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"]
    assert "autonomy_level" in data["data"]
    assert "kill_switch_active" in data["data"]


def test_create_and_run_mission_api(client: TestClient) -> None:
    create_payload = {
        "title": "API Test Mission",
        "objective": "Inspect system status",
        "autonomy_level": "SUPERVISED",
        "allowed_scope": ["data/*", "artifacts/*"],
    }

    create_resp = client.post("/api/v1/autonomy/missions", json=create_payload)
    assert create_resp.status_code == 201
    mission_id = create_resp.json()["data"]["mission_id"]

    run_resp = client.post(f"/api/v1/autonomy/missions/{mission_id}/start")
    assert run_resp.status_code == 200
    res_data = run_resp.json()
    assert res_data["success"]
    assert res_data["data"]["status"] == "COMPLETED"


def test_set_kill_switch_api(client: TestClient) -> None:
    resp = client.post("/api/v1/autonomy/kill-switch", json={"active": True})
    assert resp.status_code == 200
    assert resp.json()["data"]["kill_switch_active"] is True

    # Restore kill switch
    client.post("/api/v1/autonomy/kill-switch", json={"active": False})


def test_run_safety_tests_api(client: TestClient) -> None:
    resp = client.post("/api/v1/autonomy/safety-tests")
    assert resp.status_code == 200
    assert resp.json()["data"]["all_tests_passed"] is True
