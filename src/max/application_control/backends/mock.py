"""MockApplicationControlBackend — deterministic in-memory backend for testing.

Never launches real processes, never opens windows, never touches the OS.
Simulates the full application lifecycle with configurable canned responses.
"""

import threading
import uuid
from datetime import UTC, datetime
from typing import Any

from max.application_control.backends.base import ApplicationControlBackend
from max.application_control.domain.enums import (
    ApplicationActionFailureReason,
    ApplicationActionStatus,
    ApplicationActionType,
    ApplicationHealthStatus,
    ApplicationSource,
    ApplicationState,
    ApplicationType,
)
from max.application_control.domain.models import (
    Application,
    ApplicationActionRequest,
    ApplicationActionResult,
    ApplicationCapability,
    ApplicationExecutable,
    ApplicationInstance,
    ApplicationMetadata,
    ApplicationWindow,
)


def _now() -> datetime:
    return datetime.now(UTC)


class MockApplicationControlBackend(ApplicationControlBackend):
    """Fully deterministic mock backend that never touches the OS."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._available: bool = True
        self._installed_apps: list[Application] = []
        self._running_instances: dict[str, list[ApplicationInstance]] = {}  # app_id → instances
        self._fake_windows: dict[str, list[ApplicationWindow]] = {}  # instance_id → windows
        self._recorded_actions: list[dict[str, Any]] = []
        self._canned_results: dict[str, ApplicationActionResult] = {}  # action_type → result
        self._fail_on: set[str] = set()
        self.should_fail_launch: bool = False

        # Seed default fake applications for testing
        self._seed_default_apps()

    def _seed_default_apps(self) -> None:
        notepad = Application(
            application_id="notepad",
            name="Notepad",
            application_type=ApplicationType.DESKTOP,
            executable=ApplicationExecutable(path="C:\\Windows\\System32\\notepad.exe", filename="notepad.exe", exists=True),
        )
        calc = Application(
            application_id="calculator",
            name="Calculator",
            application_type=ApplicationType.DESKTOP,
            executable=ApplicationExecutable(path="C:\\Windows\\System32\\calc.exe", filename="calc.exe", exists=True),
        )
        self._installed_apps.extend([notepad, calc])

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    def set_available(self, available: bool) -> None:
        with self._lock:
            self._available = available

    def register_fake_application(self, app: Application) -> None:
        with self._lock:
            self._installed_apps.append(app)

    def register_fake_instance(self, app_id: str, instance: ApplicationInstance) -> None:
        with self._lock:
            self._running_instances.setdefault(app_id, []).append(instance)

    def register_fake_window(self, instance_id: str, window: ApplicationWindow) -> None:
        with self._lock:
            self._fake_windows.setdefault(instance_id, []).append(window)

    def register_canned_result(self, action_type: str, result: ApplicationActionResult) -> None:
        with self._lock:
            self._canned_results[action_type] = result

    def set_fail_on(self, *action_types: str) -> None:
        with self._lock:
            self._fail_on.update(action_types)

    def clear_fail_on(self) -> None:
        with self._lock:
            self._fail_on.clear()

    def recorded_action_count(self) -> int:
        with self._lock:
            return len(self._recorded_actions)

    def last_action(self) -> dict[str, Any] | None:
        with self._lock:
            return self._recorded_actions[-1] if self._recorded_actions else None

    def clear_recorded_actions(self) -> None:
        with self._lock:
            self._recorded_actions.clear()

    # ------------------------------------------------------------------
    # Backend interface
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        return self._available

    def discover_applications(self) -> list[Application]:
        return self.discover_installed_applications()

    def discover_installed_applications(self) -> list[Application]:
        with self._lock:
            return list(self._installed_apps)

    def discover_running_applications(self) -> list[Application]:
        with self._lock:
            apps: list[Application] = []
            for app_id, instances in self._running_instances.items():
                if instances:
                    installed = next((a for a in self._installed_apps if a.application_id == app_id), None)
                    if installed:
                        apps.append(installed)
                    else:
                        apps.append(
                            Application(
                                application_id=app_id,
                                name=app_id,
                                application_type=ApplicationType.DESKTOP,
                            )
                        )
            return apps

    def get_running_instances(self, app_id: str | None = None) -> list[ApplicationInstance]:
        with self._lock:
            if app_id:
                return list(self._running_instances.get(app_id, []))
            all_insts = []
            for insts in self._running_instances.values():
                all_insts.extend(insts)
            return all_insts

    def get_windows_for_instance(self, process_id: int) -> list[ApplicationWindow]:
        with self._lock:
            for instance_id, windows in self._fake_windows.items():
                for app_instances in self._running_instances.values():
                    for inst in app_instances:
                        if inst.process_id == process_id and inst.instance_id == instance_id:
                            return list(windows)
            # Default window for active instances if none registered
            return [
                ApplicationWindow(
                    window_id=f"win_{process_id}",
                    title="Mock Application Window",
                    process_id=process_id,
                    visible=True,
                )
            ]

    def get_application_windows(self, target: Any) -> list[ApplicationWindow]:
        pid = target.pid if hasattr(target, "pid") else getattr(target, "process_id", target if isinstance(target, int) else 0)
        return self.get_windows_for_instance(pid or 1000)

    def get_resource_usage(self, instance: ApplicationInstance) -> dict[str, Any]:
        return {
            "cpu_percent": 1.5,
            "memory_rss_bytes": 50 * 1024 * 1024,
            "memory_vms_bytes": 100 * 1024 * 1024,
        }

    def launch_application(
        self, app_or_request: Any, request: ApplicationActionRequest | None = None
    ) -> ApplicationActionResult:
        req = request or (app_or_request if isinstance(app_or_request, ApplicationActionRequest) else None)
        app = app_or_request if isinstance(app_or_request, Application) else None
        app_id = (app.app_id if app else None) or (req.application_id if req else None) or "mock_app"

        if req is None:
            req = ApplicationActionRequest(
                action_type=ApplicationActionType.LAUNCH,
                application_id=app_id,
            )

        self._record(req)

        if not self._available:
            return self._unavailable(req)
        if self.should_fail_launch or req.action_type.value in self._fail_on or "LAUNCH" in self._fail_on:
            return self._canned_fail(req, ApplicationActionFailureReason.EXECUTION_FAILED, "Simulated launch failure")

        start = _now()
        fake_pid = 10000 + len(self._recorded_actions)
        instance_id = f"inst_{uuid.uuid4().hex[:8]}"

        instance = ApplicationInstance(
            instance_id=instance_id,
            application_id=app_id,
            process_id=fake_pid,
            executable_path=app.executable.path if (app and app.executable) else "mock.exe",
            state=ApplicationState.RUNNING,
            health=ApplicationHealthStatus.RESPONDING,
        )

        with self._lock:
            self._running_instances.setdefault(app_id, []).append(instance)

        end = _now()
        return ApplicationActionResult(
            action_id=req.action_id,
            action_type=req.action_type,
            status=ApplicationActionStatus.COMPLETED,
            application_id=app_id,
            instance_id=instance_id,
            launched_instance_id=instance_id,
            previous_state=ApplicationState.NOT_RUNNING,
            resulting_state=ApplicationState.RUNNING,
            duration=(end - start).total_seconds(),
            simulated=False,
            executed_at=start,
            completed_at=end,
        )

    def focus_application(
        self, instance_or_request: Any, request: ApplicationActionRequest | None = None
    ) -> ApplicationActionResult:
        req = request or (instance_or_request if isinstance(instance_or_request, ApplicationActionRequest) else None)
        if req is None:
            req = ApplicationActionRequest(action_type=ApplicationActionType.FOCUS)
        return self._simple_lifecycle(req, ApplicationState.FOCUSED)

    def minimize_application(
        self, instance_or_request: Any, request: ApplicationActionRequest | None = None
    ) -> ApplicationActionResult:
        req = request or (instance_or_request if isinstance(instance_or_request, ApplicationActionRequest) else None)
        if req is None:
            req = ApplicationActionRequest(action_type=ApplicationActionType.MINIMIZE)
        return self._simple_lifecycle(req, ApplicationState.MINIMIZED)

    def maximize_application(
        self, instance_or_request: Any, request: ApplicationActionRequest | None = None
    ) -> ApplicationActionResult:
        req = request or (instance_or_request if isinstance(instance_or_request, ApplicationActionRequest) else None)
        if req is None:
            req = ApplicationActionRequest(action_type=ApplicationActionType.MAXIMIZE)
        return self._simple_lifecycle(req, ApplicationState.MAXIMIZED)

    def restore_application(
        self, instance_or_request: Any, request: ApplicationActionRequest | None = None
    ) -> ApplicationActionResult:
        req = request or (instance_or_request if isinstance(instance_or_request, ApplicationActionRequest) else None)
        if req is None:
            req = ApplicationActionRequest(action_type=ApplicationActionType.RESTORE)
        return self._simple_lifecycle(req, ApplicationState.RUNNING)

    def close_application(
        self, instance_or_request: Any, request: ApplicationActionRequest | None = None
    ) -> ApplicationActionResult:
        req = request or (instance_or_request if isinstance(instance_or_request, ApplicationActionRequest) else None)
        if req is None:
            req = ApplicationActionRequest(action_type=ApplicationActionType.CLOSE)

        inst = instance_or_request if isinstance(instance_or_request, ApplicationInstance) else None
        if inst:
            with self._lock:
                insts = self._running_instances.get(inst.app_id, [])
                self._running_instances[inst.app_id] = [i for i in insts if i.instance_id != inst.instance_id]

        return self._simple_lifecycle(req, ApplicationState.CLOSED)

    def force_terminate_application(
        self, instance_or_request: Any, request: ApplicationActionRequest | None = None
    ) -> ApplicationActionResult:
        req = request or (instance_or_request if isinstance(instance_or_request, ApplicationActionRequest) else None)
        if req is None:
            req = ApplicationActionRequest(action_type=ApplicationActionType.FORCE_TERMINATE)

        inst = instance_or_request if isinstance(instance_or_request, ApplicationInstance) else None
        if inst:
            with self._lock:
                insts = self._running_instances.get(inst.app_id, [])
                self._running_instances[inst.app_id] = [i for i in insts if i.instance_id != inst.instance_id]

        return self._simple_lifecycle(req, ApplicationState.STOPPED)

    def _record(self, request: ApplicationActionRequest) -> None:
        with self._lock:
            self._recorded_actions.append({
                "action_id": request.action_id,
                "action_type": request.action_type.value if hasattr(request.action_type, "value") else str(request.action_type),
                "application_id": request.application_id,
                "instance_id": request.instance_id,
                "timestamp": _now(),
            })

    def _unavailable(self, request: ApplicationActionRequest) -> ApplicationActionResult:
        return self._canned_fail(request, ApplicationActionFailureReason.BACKEND_UNAVAILABLE, "Mock backend is unavailable")

    def _canned_fail(
        self,
        request: ApplicationActionRequest,
        reason: ApplicationActionFailureReason,
        message: str,
    ) -> ApplicationActionResult:
        start = _now()
        return ApplicationActionResult(
            action_id=request.action_id,
            action_type=request.action_type,
            status=ApplicationActionStatus.FAILED,
            application_id=request.application_id,
            instance_id=request.instance_id,
            failure_reason=reason,
            failure_message=message,
            executed_at=start,
            completed_at=_now(),
        )

    def _simple_lifecycle(
        self,
        request: ApplicationActionRequest,
        resulting_state: ApplicationState,
    ) -> ApplicationActionResult:
        self._record(request)
        if not self._available:
            return self._unavailable(request)
        at = request.action_type.value if hasattr(request.action_type, "value") else str(request.action_type)
        if at in self._fail_on:
            return self._canned_fail(request, ApplicationActionFailureReason.INTERNAL_ERROR, f"Simulated {at} failure")

        start = _now()
        end = _now()
        return ApplicationActionResult(
            action_id=request.action_id,
            action_type=request.action_type,
            status=ApplicationActionStatus.COMPLETED,
            application_id=request.application_id,
            instance_id=request.instance_id,
            previous_state=ApplicationState.RUNNING,
            resulting_state=resulting_state,
            duration=(end - start).total_seconds(),
            executed_at=start,
            completed_at=end,
        )
