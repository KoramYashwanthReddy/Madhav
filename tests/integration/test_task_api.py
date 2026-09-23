"""Integration tests for Task Engine REST API endpoints."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from max.api.router import register_routers
from max.reasoning.domain.enums import CompletenessStatus, PlanStatus
from max.reasoning.domain.plan import Plan, PlanStep
from max.tasks.api.routes import get_plan_repository


@pytest.fixture
def api_client() -> TestClient:
    app = FastAPI()
    register_routers(app)
    return TestClient(app)


def test_create_and_get_task_api(api_client: TestClient) -> None:
    """Test POST /api/v1/tasks and GET /api/v1/tasks/{task_id} endpoints."""
    payload = {
        "owner_id": "user_api",
        "title": "API Test Task",
        "description": "Integration test task",
        "priority": "HIGH",
        "type": "CODING",
    }

    create_res = api_client.post("/api/v1/tasks", json=payload)
    assert create_res.status_code == 201
    data = create_res.json()
    assert data["title"] == "API Test Task"
    assert data["priority"] == "HIGH"
    task_id = data["id"]

    get_res = api_client.get(f"/api/v1/tasks/{task_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == task_id


def test_task_lifecycle_api_endpoints(api_client: TestClient) -> None:
    """Test lifecycle status transition endpoints (start, pause, resume, complete)."""
    # Create task
    create_res = api_client.post(
        "/api/v1/tasks", json={"owner_id": "u1", "title": "Lifecycle Task"}
    )
    task_id = create_res.json()["id"]

    # Start
    start_res = api_client.post(f"/api/v1/tasks/{task_id}/start")
    assert start_res.status_code == 200
    assert start_res.json()["status"] == "IN_PROGRESS"

    # Pause
    pause_res = api_client.post(f"/api/v1/tasks/{task_id}/pause")
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "PAUSED"

    # Resume
    resume_res = api_client.post(f"/api/v1/tasks/{task_id}/resume")
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] == "IN_PROGRESS"

    # Complete
    comp_res = api_client.post(f"/api/v1/tasks/{task_id}/complete")
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "COMPLETED"
    assert comp_res.json()["progress"] == 100


def test_task_group_api(api_client: TestClient) -> None:
    """Test POST /api/v1/task-groups and summary endpoints."""
    group_payload = {"owner_id": "u1", "name": "API Group", "description": "Group for testing"}
    res = api_client.post("/api/v1/task-groups", json=group_payload)
    assert res.status_code == 201
    group_id = res.json()["group_id"]

    summary_res = api_client.get(f"/api/v1/task-groups/{group_id}/summary")
    assert summary_res.status_code == 200
    assert summary_res.json()["name"] == "API Group"


def test_convert_plan_to_tasks_api(api_client: TestClient) -> None:
    """Test POST /api/v1/plans/{plan_id}/tasks endpoint."""
    plan_repo = get_plan_repository()
    plan = Plan(
        plan_id="plan_api_1",
        title="API Test Plan",
        description="API Plan Description",
        reasoning_id="reas_1",
        owner_id="u1",
        version=1,
        steps=[PlanStep(sequence=1, step_id="s1", title="Plan Step 1", description="Desc")],
        status=PlanStatus.ACTIVE,
        completeness=CompletenessStatus.COMPLETE,
    )

    plan_repo._store[plan.plan_id] = plan

    convert_res = api_client.post(f"/api/v1/plans/{plan.plan_id}/tasks")
    assert convert_res.status_code == 201
    data = convert_res.json()
    assert data["generated_tasks_count"] == 1
    assert data["tasks"][0]["title"] == "Plan Step 1"
