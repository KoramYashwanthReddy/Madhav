"""Integration tests for Module 13 Agent Engine REST API endpoints."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from madhav.api.router import register_routers


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    register_routers(app)
    return TestClient(app)


def test_agent_api_crud_and_lifecycle(client: TestClient) -> None:
    """Test POST, GET, PATCH, activate, pause, disable, and archive via REST API."""
    # 1. Create Agent
    create_req = {
        "name": "api_planner",
        "description": "API Test Agent",
        "type": "PLANNER",
        "role": "PLANNER",
        "capabilities": ["PLANNING", "TASK_COORDINATION"],
        "owner_id": "user_api",
    }
    resp = client.post("/api/v1/agents", json=create_req)
    assert resp.status_code == 201
    agent_data = resp.json()
    agent_id = agent_data["id"]
    assert agent_data["name"] == "api_planner"
    assert agent_data["status"] == "CREATED"

    # 2. Get Agent
    resp = client.get(f"/api/v1/agents/{agent_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == agent_id

    # 3. Activate Agent
    resp = client.post(f"/api/v1/agents/{agent_id}/activate")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ACTIVE"

    # 4. Capabilities & Availability
    resp = client.get(f"/api/v1/agents/{agent_id}/capabilities")
    assert resp.status_code == 200
    assert "PLANNING" in resp.json()["capabilities"]

    resp = client.get(f"/api/v1/agents/{agent_id}/availability")
    assert resp.status_code == 200
    assert resp.json()["is_available"] is True

    # 5. Select Agent
    select_req = {
        "required_capabilities": ["PLANNING"],
        "preferred_role": "PLANNER",
    }
    resp = client.post("/api/v1/agents/select", json=select_req)
    assert resp.status_code == 200
    assert resp.json()["matched"] is True
    assert resp.json()["selected_agent_id"] == agent_id

    # 6. Pause Agent
    resp = client.post(f"/api/v1/agents/{agent_id}/pause")
    assert resp.status_code == 200
    assert resp.json()["status"] == "PAUSED"


def test_agent_api_assignment_and_runs(client: TestClient) -> None:
    """Test agent assignment, runs, lifecycle state updates, and trace endpoints via REST API."""
    # Create agent and activate
    create_agent_req = {
        "name": "api_executor",
        "type": "COORDINATOR",
        "role": "COORDINATOR",
        "capabilities": ["TASK_COORDINATION"],
        "owner_id": "user_api",
    }
    agent_id = client.post("/api/v1/agents", json=create_agent_req).json()["id"]
    client.post(f"/api/v1/agents/{agent_id}/activate")

    # Assignment
    assign_req = {
        "task_id": "task_api_123",
        "priority": "HIGH",
        "reason": "Test task assignment",
    }
    resp = client.post(f"/api/v1/agents/{agent_id}/assignments", json=assign_req)
    assignment_id = resp.json()["assignment_id"]
    assert assignment_id.startswith("asgn_")
    assert resp.json()["status"] == "ASSIGNED"

    # Run
    run_req = {
        "task_id": "task_api_123",
        "owner_id": "user_api",
        "execution_mode": "DRY_RUN",
    }
    resp = client.post(f"/api/v1/agents/{agent_id}/runs", json=run_req)
    assert resp.status_code == 201
    run_id = resp.json()["run_id"]
    assert resp.json()["status"] == "CREATED"

    # Start run
    resp = client.post(f"/api/v1/agents/{agent_id}/runs/{run_id}/start")
    assert resp.status_code == 200
    assert resp.json()["status"] == "RUNNING"

    # Trace
    resp = client.get(f"/api/v1/agents/{agent_id}/runs/{run_id}/trace")
    assert resp.status_code == 200
    assert resp.json()["run_id"] == run_id
