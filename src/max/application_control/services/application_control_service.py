"""ApplicationControlService — Primary Facade Service for Module 19.

Orchestrates application discovery, lifecycle operations (launch, focus, close, restart),
window management, policy enforcement, status monitoring, and audit logging.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from max.application_control.backends.base import ApplicationControlBackend
from max.application_control.domain.enums import (
    ApplicationActionStatus,
    ApplicationActionType,
    ApplicationAuditEventType,
    ApplicationCategory,
    ApplicationStatus,
)
from max.application_control.domain.exceptions import (
    ApplicationNotFoundError,
    ApplicationProcessNotFoundError,
)
from max.application_control.domain.models import (
    Application,
    ApplicationActionRequest,
    ApplicationActionResult,
    ApplicationAuditEvent,
    ApplicationInstance,
    ApplicationPolicy,
    ApplicationWindow,
)
from max.application_control.repositories.repositories import (
    ApplicationAuditRepository,
    ApplicationInstanceRepository,
    ApplicationPolicyRepository,
    ApplicationRepository,
)
from max.application_control.security.app_policy import ApplicationPolicyService
from max.config.sections import ApplicationControlSettings

logger = logging.getLogger(__name__)


class ApplicationControlService:
    """Core domain service for Application Control."""

    def __init__(
        self,
        backend: ApplicationControlBackend,
        settings: ApplicationControlSettings | None = None,
        app_repo: ApplicationRepository | None = None,
        instance_repo: ApplicationInstanceRepository | None = None,
        policy_repo: ApplicationPolicyRepository | None = None,
        audit_repo: ApplicationAuditRepository | None = None,
        policy_service: ApplicationPolicyService | None = None,
    ) -> None:
        self.backend = backend
        self.settings = settings or ApplicationControlSettings()
        self.app_repo = app_repo or ApplicationRepository()
        self.instance_repo = instance_repo or ApplicationInstanceRepository()
        self.policy_repo = policy_repo or ApplicationPolicyRepository()
        self.audit_repo = audit_repo or ApplicationAuditRepository()
        self.policy_service = policy_service or ApplicationPolicyService(
            settings=self.settings,
            policy_repo=self.policy_repo,
            instance_repo=self.instance_repo,
        )

        # Initial discovery if catalog is empty
        if self.app_repo.count() == 0:
            try:
                self.discover_applications()
            except Exception as e:
                logger.warning("Failed initial application discovery: %s", e)

    def discover_applications(self, force_refresh: bool = False) -> list[Application]:
        """Discover applications installed on the system and sync catalog."""
        if self.app_repo.count() > 0 and not force_refresh:
            return self.app_repo.list_all()

        discovered = self.backend.discover_applications()
        self.app_repo.save_many(discovered)

        # Audit event
        self.audit_repo.record(
            ApplicationAuditEvent(
                event_type=ApplicationAuditEventType.DISCOVERED,
                details={"discovered_count": len(discovered)},
            )
        )
        return self.app_repo.list_all()

    def list_applications(
        self,
        category: ApplicationCategory | None = None,
        installed_only: bool = False,
    ) -> list[Application]:
        """List registered applications in the catalog."""
        return self.app_repo.list_all(category=category, installed_only=installed_only)

    def get_application(self, query: str) -> Application:
        """Find an application by ID, name, or executable string."""
        app = self.app_repo.get_by_name_or_executable(query)
        if not app:
            # Fallback: query backend directly for running apps or apps by executable
            discovered = self.discover_applications(force_refresh=True)
            for d in discovered:
                exe_str = d.executable.lower() if d.executable else ""
                if d.app_id == query or exe_str == query.lower() or d.display_name.lower() == query.lower():
                    return d
            raise ApplicationNotFoundError(f"Application matching '{query}' was not found.")
        return app

    def launch_application(
        self,
        query: str,
        arguments: list[str] | None = None,
        working_directory: str | None = None,
        elevate: bool = False,
        timeout: float | None = None,
    ) -> ApplicationActionResult:
        """Launch an application given an app ID, executable name, or display name."""
        app = self.get_application(query)

        # Security policy validation
        self.policy_service.validate_launch(app, elevate=elevate, args=arguments)

        req = ApplicationActionRequest(
            action_type=ApplicationActionType.LAUNCH,
            application_id=app.app_id,
            arguments=arguments or [],
            working_directory=working_directory,
            elevate=elevate,
            timeout=timeout or self.settings.default_launch_timeout,
        )

        result = self.backend.launch_application(app, req)

        # Update repos and record audit
        if result.is_success and result.instance:
            self.instance_repo.save(result.instance)
            app_updated = app.model_copy(update={"status": ApplicationStatus.RUNNING})
            self.app_repo.save(app_updated)

            self.audit_repo.record(
                ApplicationAuditEvent(
                    event_type=ApplicationAuditEventType.LAUNCHED,
                    application_id=app.app_id,
                    instance_id=result.instance.instance_id,
                    action_id=req.action_id,
                    details={"status": "SUCCESS", "pid": result.instance.pid, "arguments": arguments},
                )
            )
        else:
            self.audit_repo.record(
                ApplicationAuditEvent(
                    event_type=ApplicationAuditEventType.LAUNCH_FAILED,
                    application_id=app.app_id,
                    action_id=req.action_id,
                    details={"status": "FAILED", "error_message": result.error_message},
                )
            )

        return result

    def list_instances(
        self,
        query: str | None = None,
        active_only: bool = True,
    ) -> list[ApplicationInstance]:
        """List active/historical application instances."""
        app_id = None
        if query:
            try:
                app = self.get_application(query)
                app_id = app.app_id
            except ApplicationNotFoundError:
                app_id = query

        # Sync running instances from backend if active_only
        if active_only:
            active_instances = self.backend.get_running_instances()
            for inst in active_instances:
                self.instance_repo.save(inst)

        return self.instance_repo.list_all(app_id=app_id, active_only=active_only)

    def focus_application(self, query: str) -> ApplicationActionResult:
        """Bring an application or instance window to the foreground."""
        target = self._resolve_target(query)
        app = target["app"]
        instance = target["instance"]

        self.policy_service.validate_action(app, "app_focus")

        req = ApplicationActionRequest(
            action_type=ApplicationActionType.FOCUS,
            application_id=app.app_id,
            instance_id=instance.instance_id if instance else None,
        )

        if instance:
            result = self.backend.focus_application(instance, req)
        else:
            # Pick first active running instance
            running = self.backend.get_running_instances()
            app_insts = [i for i in running if i.app_id == app.app_id]
            if not app_insts:
                raise ApplicationProcessNotFoundError(
                    f"No active running instance of application '{app.display_name}' found to focus."
                )
            result = self.backend.focus_application(app_insts[0], req)

        if result.is_success:
            self.audit_repo.record(
                ApplicationAuditEvent(
                    event_type=ApplicationAuditEventType.FOCUSED,
                    application_id=app.app_id,
                    instance_id=instance.instance_id if instance else None,
                    action_id=req.action_id,
                    details={"status": "SUCCESS"},
                )
            )

        return result

    def close_application(
        self,
        query: str,
        graceful: bool = True,
        timeout: float = 5.0,
    ) -> ApplicationActionResult:
        """Close or terminate an application instance or all running instances of an app."""
        target = self._resolve_target(query)
        app = target["app"]
        instance = target["instance"]

        self.policy_service.validate_action(app, "app_close")

        action_type = ApplicationActionType.CLOSE if graceful else ApplicationActionType.FORCE_TERMINATE
        req = ApplicationActionRequest(
            action_type=action_type,
            application_id=app.app_id,
            instance_id=instance.instance_id if instance else None,
            graceful=graceful,
            timeout=timeout,
        )

        if instance:
            result = self.backend.close_application(instance, req)
            if result.is_success:
                updated_inst = instance.model_copy(
                    update={
                        "status": ApplicationStatus.CLOSED,
                        "exit_code": 0,
                    }
                )
                self.instance_repo.save(updated_inst)
        else:
            # Close all active instances for this app
            running = self.backend.get_running_instances()
            app_insts = [i for i in running if i.app_id == app.app_id]
            if not app_insts:
                return ApplicationActionResult(
                    action_id=req.action_id,
                    status=ApplicationActionStatus.SUCCESS,
                    message=f"No active running instances found for '{app.display_name}'.",
                )

            last_res = None
            for inst in app_insts:
                res = self.backend.close_application(inst, req)
                if res.is_success:
                    self.instance_repo.save(
                        inst.model_copy(
                            update={
                                "status": ApplicationStatus.CLOSED
                            }
                        )
                    )
                last_res = res
            result = last_res or ApplicationActionResult(
                action_id=req.action_id,
                status=ApplicationActionStatus.SUCCESS,
                message=f"Closed instances of '{app.display_name}'.",
            )

        # Check if remaining instances exist
        if self.instance_repo.count_active_for_app(app.app_id) == 0:
            self.app_repo.save(app.model_copy(update={"status": ApplicationStatus.CLOSED}))

        self.audit_repo.record(
            ApplicationAuditEvent(
                event_type=ApplicationAuditEventType.CLOSED,
                application_id=app.app_id,
                instance_id=instance.instance_id if instance else None,
                action_id=req.action_id,
                details={"status": "SUCCESS" if result.is_success else "FAILED"},
            )
        )

        return result

    def restart_application(
        self,
        query: str,
        graceful: bool = True,
        timeout: float = 5.0,
    ) -> ApplicationActionResult:
        """Restart an application by closing running instances and launching a new instance."""
        target = self._resolve_target(query)
        app = target["app"]
        target["instance"]

        self.policy_service.validate_action(app, "app_restart")

        # Close existing
        self.close_application(query=query, graceful=graceful, timeout=timeout)

        # Launch new
        return self.launch_application(query=app.app_id)

    def get_application_windows(self, query: str) -> list[ApplicationWindow]:
        """Get open windows belonging to an application or instance."""
        target = self._resolve_target(query)
        instance = target["instance"]
        app = target["app"]

        if instance:
            return self.backend.get_application_windows(instance)

        # Search windows for app_id or PIDs
        instances = self.list_instances(query=app.app_id, active_only=True)
        all_windows = []
        for inst in instances:
            all_windows.extend(self.backend.get_application_windows(inst))
        return all_windows

    def get_application_status(self, query: str) -> dict[str, Any]:
        """Get real-time operational and resource usage status for an application."""
        target = self._resolve_target(query)
        app = target["app"]
        instance = target["instance"]

        active_instances = self.list_instances(query=app.app_id, active_only=True)
        running_count = len(active_instances)

        if instance:
            usage = self.backend.get_resource_usage(instance)
            return {
                "app_id": app.app_id,
                "display_name": app.display_name,
                "instance_id": instance.instance_id,
                "pid": instance.pid,
                "status": instance.status.value,
                "is_active": instance.is_active,
                "cpu_percent": usage.get("cpu_percent", 0.0),
                "memory_rss_bytes": usage.get("memory_rss_bytes", 0),
                "memory_vms_bytes": usage.get("memory_vms_bytes", 0),
                "uptime_seconds": (
                    (datetime.now(UTC) - instance.launched_at).total_seconds()
                    if instance.launched_at
                    else 0.0
                ),
                "windows_count": len(self.backend.get_application_windows(instance)),
            }

        return {
            "app_id": app.app_id,
            "display_name": app.display_name,
            "status": app.status.value,
            "active_instances_count": running_count,
            "instances": [
                {
                    "instance_id": i.instance_id,
                    "pid": i.pid,
                    "status": i.status.value,
                    "launched_at": i.launched_at.isoformat(),
                }
                for i in active_instances
            ],
        }

    def set_application_policy(self, policy: ApplicationPolicy) -> ApplicationPolicy:
        """Update or set policy rules for an application."""
        res = self.policy_repo.save(policy)
        self.audit_repo.record(
            ApplicationAuditEvent(
                event_type=ApplicationAuditEventType.POLICY_UPDATED,
                application_id=policy.app_id,
                details={
                    "allowed": policy.allowed,
                    "allow_elevation": policy.allow_elevation,
                    "max_instances": policy.max_instances,
                },
            )
        )
        return res

    def get_audit_events(
        self,
        app_id: str | None = None,
        instance_id: str | None = None,
        limit: int = 100,
    ) -> list[ApplicationAuditEvent]:
        """Retrieve recorded audit events."""
        return self.audit_repo.list_events(app_id=app_id, instance_id=instance_id, limit=limit)

    def _resolve_target(self, query: str) -> dict[str, Any]:
        """Resolve a query string to an Application and an optional ApplicationInstance."""
        inst = self.instance_repo.get(query)
        if inst:
            app = self.app_repo.get(inst.app_id) or self.get_application(inst.app_id)
            return {"app": app, "instance": inst}

        app = self.get_application(query)
        return {"app": app, "instance": None}
