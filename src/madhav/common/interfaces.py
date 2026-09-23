"""Base interfaces and abstract protocols for MADHAV platform foundation."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ServiceLifecycle(Protocol):
    """Protocol for services requiring explicit lifecycle management."""

    async def initialize(self) -> None:
        """Initialize foundation service resources."""
        ...

    async def shutdown(self) -> None:
        """Release foundation service resources cleanly."""
        ...


@runtime_checkable
class HealthCheckProvider(Protocol):
    """Protocol for components supplying readiness/health diagnostic checks."""

    @property
    def provider_name(self) -> str:
        """Return unique health check provider identifier."""
        ...

    async def check_health(self) -> dict[str, Any]:
        """Perform component health check and return status dictionary."""
        ...
