"""Integration tests for FastAPI settings injection and runtime behavior."""

import pytest
from httpx import ASGITransport, AsyncClient

from max.config.enums import Environment
from max.config.sections import APISettings, ApplicationSettings, CORSSettings, FeatureFlags
from max.config.settings import Settings
from max.core.application import create_app


@pytest.mark.asyncio
async def test_docs_disabled_in_configuration() -> None:
    """Verify OpenAPI and interactive docs endpoints are disabled when configured."""
    custom_settings = Settings(
        application=ApplicationSettings(environment=Environment.TESTING),
        api=APISettings(docs_enabled=False, openapi_enabled=False),
        features=FeatureFlags(api_docs=False),
    )
    test_app = create_app(settings=custom_settings)

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        docs_res = await client.get("/api/v1/docs")
        assert docs_res.status_code == 404

        openapi_res = await client.get("/api/v1/openapi.json")
        assert openapi_res.status_code == 404


@pytest.mark.asyncio
async def test_cors_middleware_headers() -> None:
    """Verify CORS middleware responds with configured origin headers."""
    custom_settings = Settings(
        application=ApplicationSettings(environment=Environment.TESTING),
        cors=CORSSettings(
            enabled=True,
            allowed_origins=["http://allowed-domain.com"],
            allow_credentials=True,
        ),
    )
    test_app = create_app(settings=custom_settings)

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://testserver"
    ) as client:
        res = await client.options(
            "/health",
            headers={
                "Origin": "http://allowed-domain.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert res.status_code == 200
        assert res.headers.get("access-control-allow-origin") == "http://allowed-domain.com"
        assert res.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.asyncio
async def test_readiness_includes_environment(client: AsyncClient) -> None:
    """Verify readiness endpoint includes active environment status."""
    res = await client.get("/ready")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    assert json_data["data"]["environment"] == "testing"
