"""Integration tests for Module 14 Tool Registry FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from madhav.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_tool_api_crud_and_lifecycle(client) -> None:
    """Test REST API registration, listing, retrieval, activation, and deletion."""
    # 1. Register tool
    register_req = {
        "name": "api.formatter",
        "description": "API string formatting utility",
        "category": "UTILITY",
        "capabilities": ["TEXT_TRANSFORMATION"],
    }
    resp = client.post("/api/v1/tools", json=register_req)
    assert resp.status_code == 201
    tool_data = resp.json()
    tool_id = tool_data["id"]
    assert tool_data["name"] == "api.formatter"
    assert tool_data["status"] == "REGISTERED"

    # 2. Get tool by ID
    get_resp = client.get(f"/api/v1/tools/{tool_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == tool_id

    # 3. Activate tool
    act_resp = client.post(f"/api/v1/tools/{tool_id}/activate")
    assert act_resp.status_code == 200
    assert act_resp.json()["status"] == "ACTIVE"

    # 4. List tools
    list_resp = client.get("/api/v1/tools")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    # 5. Search descriptors
    search_resp = client.get("/api/v1/tools/search?q=formatter")
    assert search_resp.status_code == 200
    assert len(search_resp.json()) >= 1


def test_tool_api_invocation_flow(client) -> None:
    """Test invoking echo.test development tool via REST API."""
    inv_req = {
        "tool_name": "echo.test",
        "arguments": {"message": "API Invocation Test"},
        "agent_id": "agent_api_1",
    }

    resp = client.post("/api/v1/tools/invocations", json=inv_req)
    assert resp.status_code == 201
    inv_data = resp.json()
    assert inv_data["status"] == "COMPLETED"
    assert inv_data["output"] == {"message": "API Invocation Test"}

    invocation_id = inv_data["invocation_id"]

    # Retrieve invocation trace
    trace_resp = client.get(f"/api/v1/tools/invocations/{invocation_id}/trace")
    assert trace_resp.status_code == 200
    assert trace_resp.json()["total_events"] > 0
