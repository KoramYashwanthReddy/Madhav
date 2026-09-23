"""Integration tests for application creation and lifecycle management."""

import pytest

from max.common.interfaces import ServiceLifecycle
from max.core.application import create_app
from max.core.lifecycle import get_lifecycle_manager, lifespan


class MockLifecycleService(ServiceLifecycle):
    """Mock service tracking lifecycle initialization and shutdown calls."""

    def __init__(self) -> None:
        self.initialized = False
        self.shutdown_called = False

    async def initialize(self) -> None:
        self.initialized = True

    async def shutdown(self) -> None:
        self.shutdown_called = True


@pytest.mark.asyncio
async def test_application_lifecycle_events() -> None:
    """Test app initialization and shutdown lifecycle hooks execution."""
    app = create_app()
    mock_service = MockLifecycleService()

    manager = get_lifecycle_manager()
    manager.register_service(mock_service)

    async with lifespan(app):
        assert mock_service.initialized is True
        assert mock_service.shutdown_called is False

    assert mock_service.shutdown_called is True
