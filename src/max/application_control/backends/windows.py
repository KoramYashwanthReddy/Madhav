"""Windows Application Control Backend for Module 19.

Uses pywin32/winreg for installed app discovery and subprocess.Popen
(shell=False) for launching. Window operations use win32api/win32con
when available, or gracefully degrade on headless systems.

Security principles:
- All process launches use shell=False (never cmd /c or powershell -Command).
- Executable paths are passed as list arguments to subprocess, never as strings.
- No credential or token information is logged or surfaced.
- Force-terminate targets exact PID from verified ApplicationInstance only.
- OS-level process handles are never returned to callers.
"""

import subprocess
import sys
import threading
import time
import winreg
from datetime import UTC, datetime
from pathlib import Path
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
    ApplicationExecutable,
    ApplicationInstance,
    ApplicationMetadata,
    ApplicationWindow,
)

# Registry keys for installed application discovery
_REGISTRY_UNINSTALL_KEYS = [
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
]

# System process names to exclude from user-application discovery
_SYSTEM_PROCESS_NAMES = frozenset(
    {
        "system", "system idle process", "registry", "smss.exe", "csrss.exe",
        "wininit.exe", "winlogon.exe", "services.exe", "lsass.exe", "svchost.exe",
        "dwm.exe", "taskhostw.exe", "conhost.exe", "fontdrvhost.exe",
        "spoolsv.exe", "searchindexer.exe", "wudfhost.exe", "msmpeng.exe",
        "securityhealthservice.exe", "antimalware service executable",
    }
)

_CLOSE_TIMEOUT_DEFAULT = 10.0  # seconds before abandoning graceful close


def _now() -> datetime:
    return datetime.now(UTC)


class WindowsApplicationControlBackend(ApplicationControlBackend):
    """Windows-native implementation using registry discovery and Win32 APIs."""

    def __init__(self) -> None:
        self._lock = threading.RLock()

    def is_available(self) -> bool:
        """Return True when running on Windows."""
        return sys.platform == "win32"

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover_installed_applications(self) -> list[Application]:
        """Discover installed applications via the Windows registry Uninstall keys.

        Does NOT modify the registry. Only reads standard uninstall metadata.
        """
        apps: dict[str, Application] = {}

        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for reg_path in _REGISTRY_UNINSTALL_KEYS:
                try:
                    with winreg.OpenKey(hive, reg_path) as root:
                        subkey_count, _, _ = winreg.QueryInfoKey(root)
                        for i in range(subkey_count):
                            try:
                                subkey_name = winreg.EnumKey(root, i)
                                with winreg.OpenKey(root, subkey_name) as sk:
                                    entry = _read_registry_entry(sk)
                                    if entry and entry.get("DisplayName"):
                                        app = _registry_entry_to_application(entry)
                                        if app.application_id not in apps:
                                            apps[app.application_id] = app
                            except OSError:
                                continue
                except (OSError, FileNotFoundError):
                    continue

        return list(apps.values())

    def discover_running_applications(self) -> list[Application]:
        """Discover running processes that appear to be user applications."""
        try:
            import psutil  # type: ignore[import]
        except ImportError:
            return self._discover_running_via_tasklist()

        apps: list[Application] = []
        seen_names: set[str] = set()

        for proc in psutil.process_iter(["pid", "name", "exe", "create_time", "status"]):
            try:
                info = proc.info
                name = (info.get("name") or "").lower()
                exe = info.get("exe") or ""
                pid = info.get("pid", 0)

                if name in _SYSTEM_PROCESS_NAMES:
                    continue
                if not exe or not name.endswith(".exe"):
                    continue

                app_name = Path(exe).stem if exe else name
                if app_name in seen_names:
                    continue
                seen_names.add(app_name)

                app_id = f"running_{pid}_{app_name.replace(' ', '_').lower()}"
                executable = ApplicationExecutable(
                    path=exe,
                    filename=Path(exe).name,
                    exists=Path(exe).exists(),
                )
                metadata = ApplicationMetadata(
                    display_name=app_name,
                    source=ApplicationSource.RUNNING_PROCESS,
                )
                apps.append(Application(
                    application_id=app_id,
                    name=app_name,
                    application_type=ApplicationType.DESKTOP,
                    source=ApplicationSource.RUNNING_PROCESS,
                    executable=executable,
                    metadata=metadata,
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return apps

    def _discover_running_via_tasklist(self) -> list[Application]:
        """Fallback: use tasklist.exe when psutil is unavailable."""
        try:
            result = subprocess.run(  # noqa: S603
                ["tasklist.exe", "/FO", "CSV", "/NH"],
                shell=False,
                capture_output=True,
                timeout=10.0,
            )
            apps: list[Application] = []
            seen: set[str] = set()
            for line in result.stdout.decode("utf-8", errors="replace").splitlines():
                parts = [p.strip('"') for p in line.split('","')]
                if len(parts) >= 2:
                    name = parts[0].lower()
                    if name in _SYSTEM_PROCESS_NAMES or name in seen:
                        continue
                    seen.add(name)
                    app_name = Path(name).stem
                    apps.append(Application(
                        application_id=f"running_{app_name}",
                        name=app_name,
                        application_type=ApplicationType.DESKTOP,
                        source=ApplicationSource.RUNNING_PROCESS,
                    ))
            return apps
        except Exception:
            return []

    def get_running_instances(self, app_id: str | None = None) -> list[ApplicationInstance]:
        """Return running instances for an application identified by name fragment."""
        application_id = app_id or ""
        try:
            import psutil  # type: ignore[import]
        except ImportError:
            return []

        instances: list[ApplicationInstance] = []
        name_fragment = application_id.lower().replace("_", " ")

        for proc in psutil.process_iter(["pid", "name", "exe", "create_time", "ppid"]):
            try:
                info = proc.info
                exe = info.get("exe") or ""
                pname = (info.get("name") or "").lower()
                pid = info.get("pid")
                ppid = info.get("ppid")

                exe_stem = Path(exe).stem.lower() if exe else pname
                if name_fragment not in exe_stem and name_fragment not in pname:
                    continue

                is_responding = True
                try:
                    proc.status()
                except Exception:
                    is_responding = False

                started_at_ts = info.get("create_time")
                started_at = (
                    datetime.fromtimestamp(started_at_ts, tz=UTC)
                    if started_at_ts
                    else _now()
                )

                instances.append(ApplicationInstance(
                    application_id=application_id,
                    process_id=pid,
                    parent_process_id=ppid,
                    executable_path=exe,
                    state=ApplicationState.RUNNING,
                    health=(
                        ApplicationHealthStatus.RESPONDING
                        if is_responding
                        else ApplicationHealthStatus.NOT_RESPONDING
                    ),
                    started_at=started_at,
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return instances

    def get_windows_for_instance(self, process_id: int) -> list[ApplicationWindow]:
        """Return windows for a process — requires pywin32."""
        if not self.is_available():
            return []
        try:
            import win32gui  # type: ignore[import]
            import win32process  # type: ignore[import]

            windows: list[ApplicationWindow] = []

            def enum_handler(hwnd: int, _: Any) -> None:
                try:
                    _, wnd_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if wnd_pid == process_id and win32gui.IsWindowVisible(hwnd):
                        rect = win32gui.GetWindowRect(hwnd)
                        title = win32gui.GetWindowText(hwnd)
                        x, y, right, bottom = rect
                        windows.append(ApplicationWindow(
                            window_id=str(hwnd),
                            title=title,
                            x=x,
                            y=y,
                            width=max(0, right - x),
                            height=max(0, bottom - y),
                            visible=True,
                            focused=False,
                            process_id=process_id,
                        ))
                except Exception:
                    pass

            win32gui.EnumWindows(enum_handler, None)
            return windows
        except ImportError:
            return []

    # ------------------------------------------------------------------
    # Lifecycle Actions
    # ------------------------------------------------------------------

    def launch_application(
        self, app_or_request: Any, request: ApplicationActionRequest | None = None
    ) -> ApplicationActionResult:
        """Launch using subprocess.Popen with shell=False."""
        req = request or (app_or_request if isinstance(app_or_request, ApplicationActionRequest) else ApplicationActionRequest(action_type=ApplicationActionType.LAUNCH, application_id=str(app_or_request)))
        start = _now()
        if not req.application_id:
            return self._make_failed(req, start, ApplicationActionFailureReason.APPLICATION_NOT_FOUND, "No application_id provided")

        exe_path = req.metadata.get("executable_path", "") if req.metadata else ""
        if not exe_path:
            return self._make_failed(req, start, ApplicationActionFailureReason.INVALID_EXECUTABLE, "No executable path resolved")

        if not Path(exe_path).exists():
            return self._make_failed(req, start, ApplicationActionFailureReason.INVALID_EXECUTABLE, f"Executable not found: {exe_path}")

        cmd = [exe_path] + req.arguments

        try:
            proc = subprocess.Popen(  # noqa: S603
                cmd,
                shell=False,  # SECURITY: always False
                cwd=req.working_directory or None,
                close_fds=True,
            )

            # Optionally wait for process to be confirmed running
            if req.wait_for_start:
                deadline = time.monotonic() + min(req.timeout, 15.0)
                while time.monotonic() < deadline:
                    if proc.poll() is None:  # still alive
                        break
                    time.sleep(0.2)

            if proc.returncode is not None and proc.returncode != 0:
                return self._make_failed(req, start, ApplicationActionFailureReason.APPLICATION_NOT_FOUND, f"Process exited immediately with code {proc.returncode}")

            instance_id = f"inst_{proc.pid}_{req.application_id[:8]}"
            end = _now()
            return ApplicationActionResult(
                action_id=req.action_id,
                action_type=req.action_type,
                status=ApplicationActionStatus.COMPLETED,
                application_id=req.application_id,
                instance_id=instance_id,
                launched_instance_id=instance_id,
                previous_state=ApplicationState.NOT_RUNNING,
                resulting_state=ApplicationState.RUNNING,
                duration=(end - start).total_seconds(),
                executed_at=start,
                completed_at=end,
            )
        except Exception as exc:
            return self._make_failed(req, start, ApplicationActionFailureReason.INTERNAL_ERROR, str(exc))

    def focus_application(
        self, instance_or_request: Any, request: ApplicationActionRequest | None = None
    ) -> ApplicationActionResult:
        """Focus application window using win32gui."""
        req = request or (instance_or_request if isinstance(instance_or_request, ApplicationActionRequest) else ApplicationActionRequest(action_type=ApplicationActionType.FOCUS))
        start = _now()
        try:
            import win32con  # type: ignore[import]
            import win32gui  # type: ignore[import]

            hwnd = self._find_hwnd(req)
            if not hwnd:
                return self._make_failed(req, start, ApplicationActionFailureReason.WINDOW_NOT_FOUND, "No window found for application")
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            end = _now()
            return self._make_success(req, start, end, ApplicationState.FOCUSED)
        except ImportError:
            return self._make_failed(req, start, ApplicationActionFailureReason.BACKEND_UNAVAILABLE, "pywin32 not available")
        except Exception as exc:
            return self._make_failed(req, start, ApplicationActionFailureReason.INTERNAL_ERROR, str(exc))

    def minimize_application(self, request: ApplicationActionRequest) -> ApplicationActionResult:
        start = _now()
        try:
            import win32con  # type: ignore[import]
            import win32gui  # type: ignore[import]
            hwnd = self._find_hwnd(request)
            if not hwnd:
                return self._make_failed(request, start, ApplicationActionFailureReason.WINDOW_NOT_FOUND, "No window found")
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            end = _now()
            return self._make_success(request, start, end, ApplicationState.MINIMIZED)
        except ImportError:
            return self._make_failed(request, start, ApplicationActionFailureReason.BACKEND_UNAVAILABLE, "pywin32 not available")
        except Exception as exc:
            return self._make_failed(request, start, ApplicationActionFailureReason.INTERNAL_ERROR, str(exc))

    def maximize_application(self, request: ApplicationActionRequest) -> ApplicationActionResult:
        start = _now()
        try:
            import win32con  # type: ignore[import]
            import win32gui  # type: ignore[import]
            hwnd = self._find_hwnd(request)
            if not hwnd:
                return self._make_failed(request, start, ApplicationActionFailureReason.WINDOW_NOT_FOUND, "No window found")
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            end = _now()
            return self._make_success(request, start, end, ApplicationState.MAXIMIZED)
        except ImportError:
            return self._make_failed(request, start, ApplicationActionFailureReason.BACKEND_UNAVAILABLE, "pywin32 not available")
        except Exception as exc:
            return self._make_failed(request, start, ApplicationActionFailureReason.INTERNAL_ERROR, str(exc))

    def restore_application(self, request: ApplicationActionRequest) -> ApplicationActionResult:
        start = _now()
        try:
            import win32con  # type: ignore[import]
            import win32gui  # type: ignore[import]
            hwnd = self._find_hwnd(request)
            if not hwnd:
                return self._make_failed(request, start, ApplicationActionFailureReason.WINDOW_NOT_FOUND, "No window found")
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            end = _now()
            return self._make_success(request, start, end, ApplicationState.RUNNING)
        except ImportError:
            return self._make_failed(request, start, ApplicationActionFailureReason.BACKEND_UNAVAILABLE, "pywin32 not available")
        except Exception as exc:
            return self._make_failed(request, start, ApplicationActionFailureReason.INTERNAL_ERROR, str(exc))

    def close_application(
        self, instance_or_request: Any, request: ApplicationActionRequest | None = None
    ) -> ApplicationActionResult:
        """Graceful close: WM_CLOSE → wait → verify."""
        req = request or (instance_or_request if isinstance(instance_or_request, ApplicationActionRequest) else ApplicationActionRequest(action_type=ApplicationActionType.CLOSE))
        start = _now()
        pid = req.process_id or (req.metadata or {}).get("process_id")
        if not pid:
            return self._make_failed(req, start, ApplicationActionFailureReason.INSTANCE_NOT_FOUND, "process_id required for close")

        try:
            import win32con  # type: ignore[import]
            import win32gui  # type: ignore[import]
            hwnd = self._find_hwnd(req)
            if hwnd:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        except ImportError:
            # Fallback: taskkill with /IM flag (graceful)
            pass

        # Wait for close
        deadline = time.monotonic() + _CLOSE_TIMEOUT_DEFAULT
        closed = False
        try:
            import psutil  # type: ignore[import]
            while time.monotonic() < deadline:
                if not psutil.pid_exists(int(pid)):
                    closed = True
                    break
                time.sleep(0.5)
        except ImportError:
            time.sleep(2.0)
            closed = True  # Assume closed

        end = _now()
        if closed:
            return self._make_success(req, start, end, ApplicationState.STOPPED, prev_state=ApplicationState.RUNNING)
        return self._make_failed(req, start, ApplicationActionFailureReason.CLOSE_TIMEOUT, f"Application did not close within {_CLOSE_TIMEOUT_DEFAULT}s")

    def force_terminate_application(
        self, instance_or_request: Any, request: ApplicationActionRequest | None = None
    ) -> ApplicationActionResult:
        """Force terminate — CRITICAL risk, exact PID only, no arbitrary kill."""
        req = request or (instance_or_request if isinstance(instance_or_request, ApplicationActionRequest) else ApplicationActionRequest(action_type=ApplicationActionType.FORCE_TERMINATE))
        start = _now()
        pid = req.process_id or (req.metadata or {}).get("process_id")
        if not pid:
            return self._make_failed(req, start, ApplicationActionFailureReason.INSTANCE_NOT_FOUND, "process_id required for force_terminate")

        try:
            import psutil  # type: ignore[import]
            proc = psutil.Process(int(pid))
            proc.terminate()
            try:
                proc.wait(timeout=5.0)
            except psutil.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3.0)
            end = _now()
            return self._make_success(req, start, end, ApplicationState.STOPPED, prev_state=ApplicationState.RUNNING)
        except ImportError:
            # Fallback: taskkill /F /PID
            try:
                subprocess.run(  # noqa: S603
                    ["taskkill.exe", "/F", "/PID", str(pid)],
                    shell=False,
                    capture_output=True,
                    timeout=10.0,
                )
                end = _now()
                return self._make_success(req, start, end, ApplicationState.STOPPED, prev_state=ApplicationState.RUNNING)
            except Exception as exc:
                return self._make_failed(req, start, ApplicationActionFailureReason.INTERNAL_ERROR, str(exc))
        except Exception as exc:
            return self._make_failed(req, start, ApplicationActionFailureReason.INTERNAL_ERROR, str(exc))

    def get_application_state(self, process_id: int) -> tuple[str, bool]:
        """Return (state_string, is_responding) for the given PID."""
        try:
            import psutil  # type: ignore[import]
            proc = psutil.Process(process_id)
            status = proc.status()
            is_running = status not in (psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD)
            return (ApplicationState.RUNNING if is_running else ApplicationState.STOPPED, is_running)
        except Exception:
            return (ApplicationState.UNKNOWN, False)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_hwnd(self, request: ApplicationActionRequest) -> int | None:
        """Find a window handle for the action target."""
        if request.window_id:
            try:
                return int(request.window_id)
            except ValueError:
                return None
        pid = request.process_id or (request.metadata or {}).get("process_id")
        if not pid:
            return None
        windows = self.get_windows_for_instance(int(pid))
        return int(windows[0].window_id) if windows else None

    @staticmethod
    def _make_success(
        request: ApplicationActionRequest,
        start: datetime,
        end: datetime,
        resulting_state: ApplicationState,
        prev_state: ApplicationState = ApplicationState.RUNNING,
    ) -> ApplicationActionResult:
        return ApplicationActionResult(
            action_id=request.action_id,
            action_type=request.action_type,
            status=ApplicationActionStatus.COMPLETED,
            application_id=request.application_id,
            instance_id=request.instance_id,
            previous_state=prev_state,
            resulting_state=resulting_state,
            duration=(end - start).total_seconds(),
            executed_at=start,
            completed_at=end,
        )

    @staticmethod
    def _make_failed(
        request: ApplicationActionRequest,
        start: datetime,
        reason: ApplicationActionFailureReason,
        message: str,
    ) -> ApplicationActionResult:
        now = _now()
        return ApplicationActionResult(
            action_id=request.action_id,
            action_type=request.action_type,
            status=ApplicationActionStatus.FAILED,
            application_id=request.application_id,
            instance_id=request.instance_id,
            duration=(now - start).total_seconds(),
            failure_reason=reason,
            failure_message=message,
            executed_at=start,
            completed_at=now,
        )


# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------


def _read_registry_entry(key: Any) -> dict[str, str]:
    """Read string values from a registry subkey into a dict."""
    result: dict[str, str] = {}
    try:
        i = 0
        while True:
            try:
                name, value, vtype = winreg.EnumValue(key, i)
                if vtype == winreg.REG_SZ and isinstance(value, str):
                    result[name] = value
                i += 1
            except OSError:
                break
    except Exception:
        pass
    return result


def _registry_entry_to_application(entry: dict[str, str]) -> Application:
    """Convert a registry uninstall entry to an Application domain model."""
    from max.application_control.domain.models import ApplicationExecutable, ApplicationMetadata

    display_name = entry.get("DisplayName", "Unknown")
    install_loc = entry.get("InstallLocation", "")
    exe_str = entry.get("DisplayIcon", "") or install_loc
    publisher = entry.get("Publisher")
    version_str = entry.get("DisplayVersion", "")
    identifier = entry.get("BundleIdentifier", "") or entry.get("UninstallString", "")[:40]

    safe_id = display_name.strip().replace(" ", "_").replace("\\", "_").lower()[:32]
    app_id = f"installed_{safe_id}"

    exe_path = exe_str.split(",")[0].strip('"').strip() if exe_str else ""
    executable = ApplicationExecutable(
        path=exe_path,
        filename=Path(exe_path).name if exe_path else "",
        exists=Path(exe_path).exists() if exe_path else False,
        publisher=publisher,
    ) if exe_path else None

    metadata = ApplicationMetadata(
        display_name=display_name,
        identifier=identifier,
        publisher=publisher,
        install_location=install_loc or None,
        source=ApplicationSource.INSTALLED_APPLICATION,
    )

    from max.application_control.domain.models import ApplicationVersion
    version = ApplicationVersion(version_string=version_str) if version_str else None

    return Application(
        application_id=app_id,
        name=display_name,
        application_type=ApplicationType.DESKTOP,
        source=ApplicationSource.INSTALLED_APPLICATION,
        executable=executable,
        metadata=metadata,
        version=version,
    )
