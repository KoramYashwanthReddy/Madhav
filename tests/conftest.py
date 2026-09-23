"""Pytest fixtures for MAX platform foundation tests."""

from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from max.config.enums import Environment
from max.config.sections import ApplicationSettings, ServerSettings
from max.config.settings import Settings, clear_settings_cache
from max.core.application import create_app


@pytest.fixture(autouse=True)
def isolate_test_environment(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Ensure test environment isolation by setting MAX_APPLICATION__ENVIRONMENT=testing."""
    monkeypatch.setenv("MAX_APPLICATION__ENVIRONMENT", "testing")
    clear_settings_cache()
    yield
    clear_settings_cache()


@pytest.fixture
def test_settings() -> Settings:
    """Provide isolated Settings instance for testing."""
    return Settings(
        application=ApplicationSettings(
            name="MAX Test",
            environment=Environment.TESTING,
            debug=False,
        ),
        server=ServerSettings(host="127.0.0.1", port=8000),
    )


@pytest.fixture
def app(test_settings: Settings) -> FastAPI:
    """Provide a fresh FastAPI application instance for testing."""
    return create_app(settings=test_settings)


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Provide an AsyncClient for testing FastAPI endpoints."""
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://testserver",
    ) as ac:
        yield ac
