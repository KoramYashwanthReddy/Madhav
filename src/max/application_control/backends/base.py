"""Abstract base class for Application Control backends (Module 19)."""

from abc import ABC, abstractmethod
from typing import Any

from max.application_control.domain.models import (
    Application,
    ApplicationActionRequest,
    ApplicationActionResult,
    ApplicationInstance,
    ApplicationWindow,
)


class ApplicationControlBackend(ABC):
    """Abstract interface all Application Control backend implementations must satisfy."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this backend can operate on the current system."""

    def discover_applications(self) -> list[Application]:
        """Return all discovered installed applications."""
        return self.discover_installed_applications()

    @abstractmethod
    def discover_installed_applications(self) -> list[Application]:
        """Return a list of installed/registered applications on this system."""

    @abstractmethod
    def discover_running_applications(self) -> list[Application]:
        """Return applications that currently have running processes."""

    @abstractmethod
    def get_running_instances(self, app_id: str | None = None) -> list[ApplicationInstance]:
        """Return all running instances of the specified application."""

    def get_application_windows(self, target: Any) -> list[ApplicationWindow]:
        """Return windows associated with an instance or process ID."""
        pid = target.pid if hasattr(target, "pid") else getattr(target, "process_id", target if isinstance(target, int) else 0)
        return self.get_windows_for_instance(pid or 0)

    @abstractmethod
    def get_windows_for_instance(self, process_id: int) -> list[ApplicationWindow]:
        """Return windows associated with a specific process ID."""

    def get_resource_usage(self, instance: ApplicationInstance) -> dict[str, Any]:
        """Return resource usage metrics for an instance."""
        return {
            "cpu_percent": 0.0,
            "memory_rss_bytes": 1024 * 1024,
            "memory_vms_bytes": 2048 * 1024,
        }

    @abstractmethod
    def launch_application(
        self, app_or_request: Any, request: ApplicationActionRequest | None = None
    ) -> ApplicationActionResult:
        """Launch an application."""

    @abstractmethod
    def focus_application(
        self, instance_or_request: Any, request: ApplicationActionRequest | None = None
    ) -> ApplicationActionResult:
        """Bring an application window to the foreground."""

    @abstractmethod
    def close_application(
        self, instance_or_request: Any, request: ApplicationActionRequest | None = None
    ) -> ApplicationActionResult:
        """Request graceful application close."""

    @abstractmethod
    def force_terminate_application(
        self, instance_or_request: Any, request: ApplicationActionRequest | None = None
    ) -> ApplicationActionResult:
        """Forcibly terminate an application process."""
