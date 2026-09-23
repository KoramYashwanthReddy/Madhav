"""Integration tests for Module 15 REST API endpoints."""

import pytest
from fastapi.testclient import TestClient

from max.main import app
from max.security.container import reset_security_container

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_container():
    reset_security_container()
    yield
    reset_security_container()


def test_api_security_check_default_deny() -> None:
    payload = {
        "subject": {"subject_type": "AGENT", "subject_id": "agent_007"},
        "action": "WRITE",
        "resource": {"resource_type": "FILE", "resource_id": "/src/app.py", "owner_id": "owner_1"},
        "owner_id": "owner_1",
    }
    response = client.post("/api/v1/security/permissions/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "DENIED"
    assert data["reason"] == "NO_POLICY_MATCH"


def test_api_policy_crud_lifecycle() -> None:
    policy_payload = {
        "name": "Allow Read Operations",
        "description": "Allow reading project files",
        "priority": 100,
        "enabled": True,
        "scope": "GLOBAL",
        "owner_id": "owner_1",
        "rules": [
            {
                "effect": "ALLOW",
                "priority": 10,
                "reason": "Read rule",
                "action_conditions": [{"field": "action", "operator": "EQUALS", "value": "READ"}],
            }
        ],
    }

    # 1. Create policy
    create_res = client.post("/api/v1/security/policies", json=policy_payload)
    assert create_res.status_code == 201
    created_policy = create_res.json()
    policy_id = created_policy["policy_id"]
    assert created_policy["name"] == "Allow Read Operations"

    # 2. Get policy
    get_res = client.get(f"/api/v1/security/policies/{policy_id}")
    assert get_res.status_code == 200
    assert get_res.json()["policy_id"] == policy_id

    # 3. List policies
    list_res = client.get("/api/v1/security/policies?owner_id=owner_1")
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # 4. Check permission with new policy
    check_payload = {
        "subject": {"subject_type": "USER", "subject_id": "user_1"},
        "action": "READ",
        "resource": {"resource_type": "FILE", "resource_id": "/src/app.py", "owner_id": "owner_1"},
        "owner_id": "owner_1",
    }
    check_res = client.post("/api/v1/security/permissions/check", json=check_payload)
    assert check_res.status_code == 200
    assert check_res.json()["status"] == "ALLOWED"

    # 5. Delete policy
    del_res = client.delete(f"/api/v1/security/policies/{policy_id}")
    assert del_res.status_code == 204


def test_api_security_mode_and_emergency() -> None:
    # Get mode
    mode_res = client.get("/api/v1/security/mode")
    assert mode_res.status_code == 200
    assert mode_res.json()["mode"] == "NORMAL"

    # Set mode
    set_mode_res = client.post(
        "/api/v1/security/mode",
        json={"mode": "LOCKDOWN", "changed_by": "admin", "reason": "Test lockdown"},
    )
    assert set_mode_res.status_code == 200
    assert set_mode_res.json()["mode"] == "LOCKDOWN"

    # Emergency kill switch
    emerg_res = client.get("/api/v1/security/emergency")
    assert emerg_res.status_code == 200
    assert emerg_res.json()["enabled"] is False

    act_res = client.post(
        "/api/v1/security/emergency/activate", json={"activated_by": "admin", "reason": "Red alert"}
    )
    assert act_res.status_code == 200
    assert act_res.json()["enabled"] is True

    deact_res = client.post(
        "/api/v1/security/emergency/deactivate",
        json={"activated_by": "admin", "reason": "All clear"},
    )
    assert deact_res.status_code == 200
    assert deact_res.json()["enabled"] is False
