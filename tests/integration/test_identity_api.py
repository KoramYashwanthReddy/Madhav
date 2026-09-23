"""Integration tests for Identity REST API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_assistant_endpoint(client: AsyncClient) -> None:
    """Test GET /api/v1/identity/assistant endpoint."""
    res = await client.get("/api/v1/identity/assistant")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    assert json_data["data"]["name"] == "Max"
    assert "request_id" in json_data


@pytest.mark.asyncio
async def test_get_owner_endpoint(client: AsyncClient) -> None:
    """Test GET /api/v1/identity/owner endpoint."""
    res = await client.get("/api/v1/identity/owner")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    assert "owner_id" in json_data["data"]


@pytest.mark.asyncio
async def test_get_profile_endpoint(client: AsyncClient) -> None:
    """Test GET /api/v1/identity/profile endpoint."""
    res = await client.get("/api/v1/identity/profile")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    assert "identity" in json_data["data"]
    assert "preferences" in json_data["data"]
    assert "communication_preferences" in json_data["data"]
    assert "locale_preferences" in json_data["data"]


@pytest.mark.asyncio
async def test_get_summary_endpoint(client: AsyncClient) -> None:
    """Test GET /api/v1/identity/summary endpoint."""
    res = await client.get("/api/v1/identity/summary")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    assert "preferred_name" in json_data["data"]
    assert "timezone" in json_data["data"]
    assert "completion_percentage" in json_data["data"]


@pytest.mark.asyncio
async def test_get_preferences_endpoint(client: AsyncClient) -> None:
    """Test GET /api/v1/identity/preferences endpoint."""
    res = await client.get("/api/v1/identity/preferences")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    assert "preferred_response_style" in json_data["data"]


@pytest.mark.asyncio
async def test_update_profile_endpoint(client: AsyncClient) -> None:
    """Test PUT /api/v1/identity/profile endpoint."""
    payload = {
        "identity": {
            "display_name": "Test Owner",
            "email": "test.owner@example.com",
            "timezone": "Asia/Kolkata",
        },
        "preferences": {
            "preferred_response_style": "detailed",
        },
    }
    res = await client.put("/api/v1/identity/profile", json=payload)
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    assert json_data["data"]["identity"]["display_name"] == "Test Owner"
    assert json_data["data"]["identity"]["email"] == "test.owner@example.com"
    assert json_data["data"]["preferences"]["preferred_response_style"] == "detailed"


@pytest.mark.asyncio
async def test_patch_preferences_endpoint(client: AsyncClient) -> None:
    """Test PATCH /api/v1/identity/preferences endpoint."""
    res = await client.patch(
        "/api/v1/identity/preferences",
        json={"preferred_response_style": "concise"},
    )
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    assert json_data["data"]["preferred_response_style"] == "concise"


@pytest.mark.asyncio
async def test_patch_communication_endpoint(client: AsyncClient) -> None:
    """Test PATCH /api/v1/identity/communication endpoint."""
    res = await client.patch(
        "/api/v1/identity/communication",
        json={"proactive_enabled": True},
    )
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    assert json_data["data"]["proactive_enabled"] is True


@pytest.mark.asyncio
async def test_patch_locale_endpoint(client: AsyncClient) -> None:
    """Test PATCH /api/v1/identity/locale endpoint."""
    res = await client.patch(
        "/api/v1/identity/locale",
        json={"timezone": "Europe/Paris", "locale": "fr_FR"},
    )
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    assert json_data["data"]["timezone"] == "Europe/Paris"
    assert json_data["data"]["locale"] == "fr_FR"


@pytest.mark.asyncio
async def test_get_completeness_endpoint(client: AsyncClient) -> None:
    """Test GET /api/v1/identity/completeness endpoint."""
    res = await client.get("/api/v1/identity/completeness")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    assert "completion_percentage" in json_data["data"]
    assert isinstance(json_data["data"]["missing_recommended_fields"], list)


@pytest.mark.asyncio
async def test_invalid_profile_update_validation(client: AsyncClient) -> None:
    """Test updating profile with invalid timezone returns 400 Bad Request."""
    payload = {
        "identity": {
            "timezone": "Invalid/Timezone_String",
        }
    }
    res = await client.put("/api/v1/identity/profile", json=payload)
    assert res.status_code == 400
    json_data = res.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "INVALID_PREFERENCE"
