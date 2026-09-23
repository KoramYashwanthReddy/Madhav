"""Integration tests for Module 06 Context Management REST API endpoints."""

from fastapi.testclient import TestClient

from madhav.main import app

client = TestClient(app)


def test_list_context_sources_endpoint() -> None:
    """Test GET /api/v1/context/sources endpoint."""
    response = client.get("/api/v1/context/sources")
    assert response.status_code == 200

    data = response.json()
    assert "sources" in data
    assert "total" in data
    assert data["total"] >= 3

    source_ids = [s["source_id"] for s in data["sources"]]
    assert "system_default" in source_ids
    assert "identity_source" in source_ids
    assert "user_request_source" in source_ids


def test_list_context_policies_endpoint() -> None:
    """Test GET /api/v1/context/policies endpoint."""
    response = client.get("/api/v1/context/policies")
    assert response.status_code == 200

    data = response.json()
    assert "policies" in data
    policy_names = [p["name"] for p in data["policies"]]
    assert "default" in policy_names
    assert "minimal" in policy_names
    assert "full" in policy_names


def test_build_context_package_endpoint_success() -> None:
    """Test POST /api/v1/context/build with valid payload."""
    payload = {
        "user_request": "Explain relativity briefly.",
        "model_reference": "development-stub",
        "policy_name": "default",
        "allow_sensitive_identity": False,
    }

    response = client.post("/api/v1/context/build", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "request_id" in data
    assert data["item_count"] >= 1
    assert data["message_count"] >= 1
    assert data["token_estimate"] > 0
    assert data["policy_used"] == "default"


def test_build_context_package_endpoint_validation_failure() -> None:
    """Test POST /api/v1/context/build with empty request payload."""
    payload = {
        "user_request": "   ",
        "policy_name": "default",
    }

    response = client.post("/api/v1/context/build", json=payload)
    assert response.status_code in {400, 422}
    data = response.json()
    assert "error" in data or "detail" in data

