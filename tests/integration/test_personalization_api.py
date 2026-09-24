"""Integration tests for Module 31 REST API endpoints and module integrations."""

import pytest
from fastapi.testclient import TestClient

from max.main import app
from max.personalization.container import PersonalizationContainer


@pytest.fixture(autouse=True)
def reset_container():
    PersonalizationContainer.reset_instance()
    yield
    PersonalizationContainer.reset_instance()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_get_profile_endpoint(client: TestClient):
    """Test GET /api/v1/personalization/profile."""
    res = client.get("/api/v1/personalization/profile?owner_id=user1")
    assert res.status_code == 200
    data = res.json()
    assert data["owner_id"] == "user1"
    assert "communication_profile" in data
    assert "notification_profile" in data
    assert "proactivity_profile" in data


def test_preference_crud_endpoints(client: TestClient):
    """Test POST, GET, PUT, DELETE /api/v1/personalization/preferences."""
    # 1. Create
    payload = {
        "category": "COMMUNICATION",
        "key": "response_length",
        "value": "short",
        "source": "EXPLICIT_USER",
    }
    create_res = client.post("/api/v1/personalization/preferences?owner_id=user1", json=payload)
    assert create_res.status_code == 201
    pref_data = create_res.json()
    pref_id = pref_data["preference_id"]
    assert pref_data["value"] == "short"

    # 2. List
    list_res = client.get("/api/v1/personalization/preferences?owner_id=user1")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 3. Get single
    get_res = client.get(f"/api/v1/personalization/preferences/{pref_id}?owner_id=user1")
    assert get_res.status_code == 200
    assert get_res.json()["key"] == "response_length"

    # 4. Update
    update_res = client.put(
        f"/api/v1/personalization/preferences/{pref_id}?owner_id=user1", json={"value": "long"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["value"] == "long"

    # 5. Delete
    del_res = client.delete(f"/api/v1/personalization/preferences/{pref_id}?owner_id=user1")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True


def test_preference_confirm_and_reject_endpoints(client: TestClient):
    """Test POST confirm and reject endpoints."""
    # Create preference
    payload = {
        "category": "NOTIFICATION",
        "key": "priority_threshold",
        "value": "HIGH",
        "source": "OBSERVED_BEHAVIOR",
    }
    pref_id = client.post("/api/v1/personalization/preferences?owner_id=user1", json=payload).json()["preference_id"]

    # Confirm
    conf_res = client.post(f"/api/v1/personalization/preferences/{pref_id}/confirm?owner_id=user1")
    assert conf_res.status_code == 200
    assert conf_res.json()["confidence"] == 1.0

    # Reject another
    pref_id2 = client.post("/api/v1/personalization/preferences?owner_id=user1", json=payload).json()["preference_id"]
    rej_res = client.post(f"/api/v1/personalization/preferences/{pref_id2}/reject?owner_id=user1")
    assert rej_res.status_code == 200


def test_settings_and_pause_resume_endpoints(client: TestClient):
    """Test GET/PUT settings and pause/resume learning endpoints."""
    get_res = client.get("/api/v1/personalization/settings")
    assert get_res.status_code == 200
    assert get_res.json()["learning_enabled"] is True

    pause_res = client.post("/api/v1/personalization/pause-learning?owner_id=user1")
    assert pause_res.status_code == 200
    assert pause_res.json()["learning_enabled"] is False

    resume_res = client.post("/api/v1/personalization/resume-learning?owner_id=user1")
    assert resume_res.status_code == 200
    assert resume_res.json()["learning_enabled"] is True


def test_simulate_endpoint(client: TestClient):
    """Test POST /api/v1/personalization/simulate dry-run."""
    sim_payload = {
        "source": "CONVERSATION",
        "signal_type": "answer_expanded",
        "payload_reference": {},
    }
    res = client.post("/api/v1/personalization/simulate?owner_id=user1", json=sim_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["observation"] is not None
    assert "detail_level" in str(data["observation"])


def test_reset_inferred_and_category_endpoints(client: TestClient):
    """Test POST reset-inferred and reset-category endpoints."""
    # Reset inferred
    res1 = client.post("/api/v1/personalization/reset-inferred?owner_id=user1")
    assert res1.status_code == 200

    # Reset category
    res2 = client.post(
        "/api/v1/personalization/reset-category?owner_id=user1", json={"category": "COMMUNICATION"}
    )
    assert res2.status_code == 200
