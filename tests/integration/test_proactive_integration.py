"""Integration tests for Module 30 — Proactive Intelligence Engine."""

import pytest
from fastapi.testclient import TestClient

from max.main import app
from max.proactive.container import ProactiveContainer


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_proactive() -> None:
    ProactiveContainer.reset_instance()


@pytest.mark.asyncio
async def test_proactive_api_status(client: TestClient) -> None:
    """Test GET /api/v1/proactive/status API endpoint."""
    res = client.get("/api/v1/proactive/status")
    assert res.status_code == 200
    data = res.json()
    assert data["enabled"] is True
    assert "user_state" in data
    assert "hourly_notifications_remaining" in data


@pytest.mark.asyncio
async def test_proactive_api_signal_ingestion(client: TestClient) -> None:
    """Test POST /api/v1/proactive/signals API endpoint."""
    payload = {
        "source": "GITHUB",
        "signal_type": "github.pull_request_review_requested",
        "payload_reference": {"pr_id": 42, "repo": "madhav/max"},
        "importance_hint": "HIGH",
    }
    res = client.post("/api/v1/proactive/signals", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["signal"]["source"] == "GITHUB"
    assert data["candidates_count"] >= 1


@pytest.mark.asyncio
async def test_proactive_api_candidates_and_decisions(client: TestClient) -> None:
    """Test candidate listing and decision listing API endpoints."""
    # 1. Ingest signal
    payload = {
        "source": "CALENDAR",
        "signal_type": "calendar.meeting_approaching",
        "payload_reference": {"title": "Architecture Sync"},
        "importance_hint": "MEDIUM",
    }
    client.post("/api/v1/proactive/signals", json=payload)

    # 2. Get candidates
    cand_res = client.get("/api/v1/proactive/candidates")
    assert cand_res.status_code == 200
    cands_data = cand_res.json()
    assert cands_data["total"] >= 1

    # 3. Get decisions
    dec_res = client.get("/api/v1/proactive/decisions")
    assert dec_res.status_code == 200
    decs_data = dec_res.json()
    assert decs_data["total"] >= 1


@pytest.mark.asyncio
async def test_proactive_api_rules_crud(client: TestClient) -> None:
    """Test creation, listing, enabling, and disabling of proactive rules via API."""
    rule_payload = {
        "name": "GitHub PR Auto-Notify",
        "description": "Notify on high importance GitHub PR reviews",
        "source": "GITHUB",
        "candidate_type": "github.pull_request_review_requested",
        "min_importance": "HIGH",
        "decision_type": "NOTIFY",
        "priority": "USER_EXPLICIT",
    }

    # 1. Create rule
    create_res = client.post("/api/v1/proactive/rules", json=rule_payload)
    assert create_res.status_code == 201
    rule_data = create_res.json()
    rule_id = rule_data["rule_id"]

    # 2. List rules
    list_res = client.get("/api/v1/proactive/rules")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 3. Disable rule
    dis_res = client.post(f"/api/v1/proactive/rules/{rule_id}/disable")
    assert dis_res.status_code == 200
    assert dis_res.json()["status"] == "DISABLED"

    # 4. Enable rule
    en_res = client.post(f"/api/v1/proactive/rules/{rule_id}/enable")
    assert en_res.status_code == 200
    assert en_res.json()["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_proactive_api_simulation(client: TestClient) -> None:
    """Test POST /api/v1/proactive/simulate API endpoint."""
    payload = {
        "source": "TASK",
        "signal_type": "task.overdue",
        "payload_reference": {"task_id": "123", "title": "Deploy hotfix"},
        "importance_hint": "HIGH",
    }
    res = client.post("/api/v1/proactive/simulate", json=payload)
    assert res.status_code == 200
    sim_data = res.json()
    assert sim_data["signal"]["source"] == "TASK"
    assert len(sim_data["candidates"]) >= 1
    assert sim_data["decision"] is not None
