"""Pytest fixtures for MADHAV platform tests."""

from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from madhav.config.enums import Environment
from madhav.config.loader import clear_settings_cache, load_settings
from madhav.config.settings import Settings
from madhav.core.application import create_app


@pytest.fixture(autouse=True)
def isolate_test_environment(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Autouse fixture ensuring test isolation from local environment variables or .env file."""
    monkeypatch.setenv("MADHAV_ENVIRONMENT", Environment.TESTING)
    clear_settings_cache()
    yield
    clear_settings_cache()


@pytest.fixture
def test_settings() -> Settings:
    """Provide deterministic test Settings instance."""
    return load_settings(
        env_overrides={
            "application": {"environment": Environment.TESTING, "debug": False},
            "server": {"port": 8000},
        }
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
