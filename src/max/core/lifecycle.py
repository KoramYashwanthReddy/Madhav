"""Application lifecycle management using FastAPI lifespan mechanism."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from max.common.interfaces import ServiceLifecycle
from max.version import APP_NAME, SERVICE_NAME, VERSION

logger = logging.getLogger("max.lifecycle")


class LifecycleManager:
    """Manages registered foundation services lifecycle hooks."""

    def __init__(self) -> None:
        self._services: list[ServiceLifecycle] = []

    def register_service(self, service: ServiceLifecycle) -> None:
        """Register a service implementing ServiceLifecycle interface."""
        self._services.append(service)

    async def initialize_all(self) -> None:
        """Initialize all registered foundation services."""
        logger.info(
            "Starting %s (%s) platform version %s",
            APP_NAME,
            SERVICE_NAME,
            VERSION,
        )
        for service in self._services:
            try:
                await service.initialize()
            except Exception:
                logger.exception("Failed initializing service %s", type(service).__name__)
                raise

    async def shutdown_all(self) -> None:
        """Gracefully release all registered foundation services."""
        logger.info("Shutting down %s platform", APP_NAME)
        for service in reversed(self._services):
            try:
                await service.shutdown()
            except Exception:
                logger.exception("Error releasing service %s", type(service).__name__)


_global_lifecycle_manager = LifecycleManager()


def get_lifecycle_manager() -> LifecycleManager:
    """Retrieve global lifecycle manager instance."""
    return _global_lifecycle_manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI application lifespan context manager for startup and shutdown events."""
    manager = get_lifecycle_manager()
    await manager.initialize_all()
    try:
        yield
    finally:
        await manager.shutdown_all()
