"""Repositories for Module 19 — Application Control.

Provides thread-safe in-memory repositories for applications, instances,
policies, and audit logs.
"""

from collections.abc import Sequence
from threading import RLock

from max.application_control.domain.enums import ApplicationCategory
from max.application_control.domain.models import (
    Application,
    ApplicationAuditEvent,
    ApplicationInstance,
    ApplicationPolicy,
)


class ApplicationRepository:
    """Thread-safe repository for discovered and managed Application catalog entries."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._apps: dict[str, Application] = {}

    def save(self, app: Application) -> Application:
        """Save or update an application profile."""
        with self._lock:
            self._apps[app.app_id] = app
            return app

    def save_many(self, apps: Sequence[Application]) -> list[Application]:
        """Bulk save application profiles."""
        with self._lock:
            for app in apps:
                self._apps[app.app_id] = app
            return list(apps)

    def get(self, app_id: str) -> Application | None:
        """Get application by exact app_id."""
        with self._lock:
            return self._apps.get(app_id)

    def get_by_name_or_executable(self, query: str) -> Application | None:
        """Find an application matching name, app_id, or executable name (case-insensitive)."""
        q = query.strip().lower()
        with self._lock:
            # Exact match on app_id
            if q in self._apps:
                return self._apps[q]

            # Match executable name or display name
            for app in self._apps.values():
                exe_str = app.executable.filename.lower() if app.executable else ""
                if exe_str == q or exe_str == f"{q}.exe":
                    return app
                if app.display_name.lower() == q:
                    return app

            # Substring match on display name or executable
            for app in self._apps.values():
                exe_str = app.executable.filename.lower() if app.executable else ""
                if q in app.display_name.lower() or (exe_str and q in exe_str):
                    return app

            return None

    def list_all(
        self,
        category: ApplicationCategory | None = None,
        installed_only: bool = False,
    ) -> list[Application]:
        """List all applications with optional filtering."""
        with self._lock:
            results = list(self._apps.values())
            if category:
                results = [a for a in results if a.category == category]
            if installed_only:
                results = [a for a in results if a.is_installed]
            return results

    def count(self) -> int:
        """Return total count of registered applications."""
        with self._lock:
            return len(self._apps)

    def delete(self, app_id: str) -> bool:
        """Delete an application entry from catalog."""
        with self._lock:
            if app_id in self._apps:
                del self._apps[app_id]
                return True
            return False

    def clear(self) -> None:
        """Clear all stored applications."""
        with self._lock:
            self._apps.clear()


class ApplicationInstanceRepository:
    """Thread-safe repository for tracked active and historical application instances."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._instances: dict[str, ApplicationInstance] = {}

    def save(self, instance: ApplicationInstance) -> ApplicationInstance:
        """Save or update an application instance."""
        with self._lock:
            self._instances[instance.instance_id] = instance
            return instance

    def get(self, instance_id: str) -> ApplicationInstance | None:
        """Get instance by instance_id."""
        with self._lock:
            return self._instances.get(instance_id)

    def get_by_pid(self, pid: int) -> ApplicationInstance | None:
        """Get active instance by PID."""
        with self._lock:
            for inst in self._instances.values():
                if inst.is_active and inst.pid == pid:
                    return inst
            return None

    def list_all(
        self,
        app_id: str | None = None,
        active_only: bool = False,
    ) -> list[ApplicationInstance]:
        """List application instances with optional filters."""
        with self._lock:
            results = list(self._instances.values())
            if app_id:
                results = [i for i in results if i.app_id == app_id]
            if active_only:
                results = [i for i in results if i.is_active]
            return results

    def count_active_for_app(self, app_id: str) -> int:
        """Count active running instances for a specific app_id."""
        with self._lock:
            return sum(
                1 for i in self._instances.values() if i.app_id == app_id and i.is_active
            )

    def delete(self, instance_id: str) -> bool:
        """Delete an instance record."""
        with self._lock:
            if instance_id in self._instances:
                del self._instances[instance_id]
                return True
            return False

    def clear(self) -> None:
        """Clear all instance records."""
        with self._lock:
            self._instances.clear()


class ApplicationPolicyRepository:
    """Thread-safe repository for per-application execution safety policies."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._policies: dict[str, ApplicationPolicy] = {}

    def save(self, policy: ApplicationPolicy) -> ApplicationPolicy:
        """Save or update an application policy rule."""
        with self._lock:
            self._policies[policy.app_id] = policy
            return policy

    def get(self, app_id: str) -> ApplicationPolicy | None:
        """Get policy rule for app_id."""
        with self._lock:
            return self._policies.get(app_id)

    def list_all(self) -> list[ApplicationPolicy]:
        """List all application policies."""
        with self._lock:
            return list(self._policies.values())

    def delete(self, app_id: str) -> bool:
        """Delete policy rule for app_id."""
        with self._lock:
            if app_id in self._policies:
                del self._policies[app_id]
                return True
            return False

    def clear(self) -> None:
        """Clear all policy rules."""
        with self._lock:
            self._policies.clear()


class ApplicationAuditRepository:
    """Thread-safe append-only audit repository for recording application control events."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._events: list[ApplicationAuditEvent] = []

    def record(self, event: ApplicationAuditEvent) -> ApplicationAuditEvent:
        """Record an audit log event."""
        with self._lock:
            self._events.append(event)
            return event

    def list_events(
        self,
        app_id: str | None = None,
        instance_id: str | None = None,
        limit: int = 100,
    ) -> list[ApplicationAuditEvent]:
        """List audit events ordered by timestamp descending."""
        with self._lock:
            results = list(self._events)
            if app_id:
                results = [e for e in results if e.app_id == app_id]
            if instance_id:
                results = [e for e in results if e.instance_id == instance_id]

            results.sort(key=lambda e: e.timestamp, reverse=True)
            return results[:limit]

    def count(self) -> int:
        """Count recorded audit events."""
        with self._lock:
            return len(self._events)

    def clear(self) -> None:
        """Clear all audit events."""
        with self._lock:
            self._events.clear()
