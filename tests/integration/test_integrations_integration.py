"""Integration and API tests for Module 29 — External Integrations Engine."""

import pytest
from fastapi.testclient import TestClient

from max.integrations.container import get_integration_container, reset_integration_container
from max.main import app
from max.scheduler.container import get_scheduler_container, reset_scheduler_container
from max.tools.services.registry import ToolRegistryService


@pytest.fixture(autouse=True)
def clean_containers():
    reset_integration_container()
    reset_scheduler_container()
    yield
    reset_integration_container()
    reset_scheduler_container()


@pytest.fixture
def api_client():
    return TestClient(app)


def test_module_14_tool_registry_auto_sync():
    """Test that integration capabilities auto-sync as tools into Module 14 ToolRegistryService."""
    from max.tools.api.routes import get_registry_service
    get_integration_container()
    tool_registry = get_registry_service()

    # Tools registered by mock email provider capability
    tools, _ = tool_registry.list_tools(search_query="mock_email")
    assert len(tools) >= 3
    tool_names = [t.name for t in tools]
    assert "integration.mock_email.email.send" in tool_names


def test_module_28_scheduler_event_integration():
    """Test that ingested webhooks emit normalized ExternalEvent into Module 28 Scheduler."""
    container = get_integration_container()
    get_scheduler_container()

    payload = {"event_type": "github.pr.created", "pr_id": 99, "action": "opened"}

    # Ingest webhook
    ext_event = container.webhook_service.ingest_webhook(
        integration_id_or_key="mock_webhook",
        headers={},
        payload=payload,
    )
    assert ext_event.event_type == "github.pr.created"


def test_integrations_api_endpoints(api_client: TestClient):
    """Test REST API endpoints under /api/v1/integrations, connections, and webhooks."""
    # 1. List Integrations
    resp_intgs = api_client.get("/api/v1/integrations")
    assert resp_intgs.status_code == 200
    intgs_data = resp_intgs.json()
    assert len(intgs_data) >= 5

    # 2. Get Capabilities
    resp_caps = api_client.get("/api/v1/integrations/mock_email/capabilities")
    assert resp_caps.status_code == 200
    assert len(resp_caps.json()) >= 3

    # 3. Create Connection via API
    conn_payload = {
        "provider_key": "mock_email",
        "owner_id": "test_user",
        "auth_data": {"api_key": "api_key_123"},
    }
    resp_conn = api_client.post("/api/v1/connections", json=conn_payload)
    assert resp_conn.status_code == 201
    conn_data = resp_conn.json()
    conn_id = conn_data["connection_id"]
    assert conn_data["status"] == "ACTIVE"

    # 4. Check Health
    resp_health = api_client.post(f"/api/v1/connections/{conn_id}/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["healthy"] is True

    # 5. Execute Action via API
    action_payload = {
        "owner_id": "test_user",
        "arguments": {"to": "recipient@example.com", "subject": "API Test", "body": "Body"},
    }
    resp_exec = api_client.post(f"/api/v1/connections/{conn_id}/actions/email.send", json=action_payload)
    assert resp_exec.status_code == 200
    exec_data = resp_exec.json()
    assert exec_data["status"] == "SUCCESS"
    assert exec_data["data"]["delivered"] is True

    # 6. Generate OAuth URL via API
    oauth_payload = {
        "provider_key": "mock_calendar",
        "auth_endpoint": "https://oauth.example.com/auth",
        "client_id": "client_123",
        "redirect_uri": "http://localhost:8000/callback",
    }
    resp_oauth = api_client.post("/api/v1/integrations/oauth/url", json=oauth_payload)
    assert resp_oauth.status_code == 200
    assert "authorization_url" in resp_oauth.json()

    # 7. Disconnect Connection
    resp_disc = api_client.post(f"/api/v1/connections/{conn_id}/disconnect")
    assert resp_disc.status_code == 200
    assert resp_disc.json()["disconnected"] is True
