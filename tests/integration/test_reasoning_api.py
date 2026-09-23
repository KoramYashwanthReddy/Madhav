"""Integration tests for Reasoning and Planning REST API routes."""

from fastapi.testclient import TestClient

from madhav.main import create_app


def test_reasoning_api_flow() -> None:
    """Test full reasoning request and result API workflow."""
    app = create_app()
    client = TestClient(app)

    # 1. Create Reasoning Request
    payload = {
        "owner_id": "user_api_1",
        "objective": {
            "title": "Build Architecture",
            "description": "Structure microservice architecture",
            "desired_outcome": "Clean architecture diagram",
            "priority": 1,
        },
        "mode": "PLANNING",
        "plan_depth": 3,
    }
    resp = client.post("/api/v1/reasoning", json=payload)
    assert resp.status_code in (200, 201)
    data = resp.json()
    reasoning_id = data["request_id"]
    assert data["status"] == "COMPLETED"
    assert data["objective_summary"] == "Build Architecture"
    assert "plan" in data
    assert len(data["plan"]["steps"]) > 0

    # 2. Retrieve Reasoning Result
    get_resp = client.get(f"/api/v1/reasoning/{reasoning_id}?owner_id=user_api_1")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["request_id"] == reasoning_id

    # 3. Retrieve Summary
    sum_resp = client.get(f"/api/v1/reasoning/{reasoning_id}/summary?owner_id=user_api_1")
    assert sum_resp.status_code == 200
    sum_data = sum_resp.json()
    assert sum_data["reasoning_id"] == reasoning_id
    assert "explanation" in sum_data

    # 4. Validate Plan via Reasoning API
    val_resp = client.post(f"/api/v1/reasoning/{reasoning_id}/validate?owner_id=user_api_1")
    assert val_resp.status_code == 200
    val_data = val_resp.json()
    assert val_data["is_valid"] is True


def test_plan_api_versioning_and_revision_flow() -> None:
    """Test plan API endpoints for creation, version retrieval, and revision."""
    app = create_app()
    client = TestClient(app)

    # 1. Create Plan
    plan_payload = {
        "owner_id": "user_api_2",
        "title": "API Test Plan",
        "description": "Test plan endpoints",
        "steps": [
            {
                "sequence": 1,
                "title": "Step A",
                "description": "First step description",
            }
        ],
    }
    create_resp = client.post("/api/v1/plans", json=plan_payload)
    assert create_resp.status_code in (200, 201)
    plan_data = create_resp.json()
    plan_id = plan_data["plan_id"]
    assert plan_data["version"] == 1

    # 2. Get Plan
    get_resp = client.get(f"/api/v1/plans/{plan_id}?owner_id=user_api_2")
    assert get_resp.status_code == 200
    assert get_resp.json()["plan_id"] == plan_id

    # 3. Revise Plan
    revise_payload = {
        "reason_for_change": "Adding step B via API",
        "steps": [
            {
                "sequence": 1,
                "title": "Step A",
                "description": "First step description",
            },
            {
                "sequence": 2,
                "title": "Step B",
                "description": "Second step added in revision",
            },
        ],
    }
    rev_resp = client.post(
        f"/api/v1/plans/{plan_id}/revise?owner_id=user_api_2", json=revise_payload
    )
    assert rev_resp.status_code == 200
    rev_data = rev_resp.json()
    assert rev_data["version"] == 2
    assert len(rev_data["steps"]) == 2

    # 4. Get Versions
    ver_resp = client.get(f"/api/v1/plans/{plan_id}/versions?owner_id=user_api_2")
    assert ver_resp.status_code == 200
    ver_data = ver_resp.json()
    assert len(ver_data) == 2
