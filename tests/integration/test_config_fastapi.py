"""Integration tests for FastAPI application driven by Settings."""

import pytest
from httpx import ASGITransport, AsyncClient

from madhav.config.enums import Environment
from madhav.config.loader import load_settings
from madhav.core.application import create_app


@pytest.mark.asyncio
async def test_fastapi_environment_in_ready_endpoint() -> None:
    """Test environment metadata returned by /ready probe."""
    settings = load_settings(
        env_overrides={
            "application": {"environment": Environment.TESTING},
        }
    )
    app = create_app(settings=settings)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        res = await client.get("/ready")
        assert res.status_code == 200
        json_data = res.json()
        assert json_data["data"]["environment"] == "testing"


@pytest.mark.asyncio
async def test_fastapi_docs_disabling_via_settings() -> None:
    """Test docs_enabled=False disables /docs and /redoc endpoints."""
    settings = load_settings(
        env_overrides={
            "api": {"docs_enabled": False, "redoc_enabled": False, "openapi_enabled": False},
            "features": {"api_docs": False},
        }
    )
    app = create_app(settings=settings)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        docs_res = await client.get("/docs")
        assert docs_res.status_code == 404

        redoc_res = await client.get("/redoc")
        assert redoc_res.status_code == 404

        openapi_res = await client.get("/openapi.json")
        assert openapi_res.status_code == 404


@pytest.mark.asyncio
async def test_cors_headers_with_settings() -> None:
    """Test CORS headers match configured allowed origins."""
    settings = load_settings(
        env_overrides={
            "cors": {
                "enabled": True,
                "allowed_origins": ["http://client.example.com"],
                "allow_credentials": True,
            }
        }
    )
    app = create_app(settings=settings)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        res = await client.options(
            "/health",
            headers={
                "Origin": "http://client.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert res.headers.get("access-control-allow-origin") == "http://client.example.com"
