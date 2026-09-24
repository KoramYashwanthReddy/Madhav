"""WSL (Windows Subsystem for Linux) terminal backend for Module 18.

Executes commands inside a WSL distribution via `wsl.exe`.

Security principles:
- shell=False enforced; command + args passed as explicit list to wsl.exe.
- Environment redaction applied identically to the Windows backend.
- stdout/stderr treated as untrusted data; sanitized and truncated.
"""

import subprocess
import threading
from datetime import UTC, datetime
from pathlib import Path

from max.terminal.backends.base import TerminalBackend
from max.terminal.backends.windows import _MAX_OUTPUT_BYTES  # shared constant
from max.terminal.backends.windows import _build_safe_env, _sanitize_output
from max.terminal.domain.enums import CommandFailureReason, CommandStatus, TerminalShell
from max.terminal.domain.models import CommandRequest, CommandResult


class WSLTerminalBackend(TerminalBackend):
    """Executes commands inside WSL using wsl.exe as the host bridge.

    Command + args are passed as explicit arguments to wsl.exe; the user
    command is never interpolated into a shell string.
    """

    def __init__(self, distribution: str | None = None) -> None:
        """Initialize WSL backend.

        Args:
            distribution: WSL distribution name (e.g. 'Ubuntu').
                          If None, the default WSL distribution is used.
        """
        self._distribution = distribution
        self._lock = threading.RLock()

    def is_available(self) -> bool:
        """Return True if wsl.exe is accessible on this system."""
        try:
            result = subprocess.run(  # noqa: S603
                ["wsl.exe", "--status"],
                shell=False,
                capture_output=True,
                timeout=5.0,
            )
            return result.returncode == 0
        except Exception:
            return False

    def execute(self, request: CommandRequest) -> CommandResult:
        """Execute a command inside WSL."""
        start = datetime.now(UTC)

        # Build wsl.exe invocation: wsl.exe [-d distribution] -- command [args...]
        wsl_cmd: list[str] = ["wsl.exe"]
        if self._distribution:
            wsl_cmd += ["-d", self._distribution]
        wsl_cmd.append("--")
        wsl_cmd.append(request.command)
        wsl_cmd.extend(request.args)

        # Validate working directory
        cwd: str | None = None
        if request.working_directory:
            wd_path = Path(request.working_directory)
            if not wd_path.exists() or not wd_path.is_dir():
                return _make_failed_result(
                    request=request,
                    start=start,
                    reason=CommandFailureReason.WORKING_DIR_VIOLATION,
                    message=f"Working directory '{request.working_directory}' does not exist.",
                )
            cwd = str(wd_path.resolve())

        safe_env = _build_safe_env(request.environment)

        try:
            with self._lock:
                proc = subprocess.run(  # noqa: S603
                    wsl_cmd,
                    shell=False,
                    capture_output=True,
                    timeout=request.timeout,
                    cwd=cwd,
                    env=safe_env,
                    input=request.stdin_data.encode("utf-8") if request.stdin_data else None,
                )

            end = datetime.now(UTC)
            stdout = _sanitize_output(proc.stdout)
            stderr = _sanitize_output(proc.stderr)

            return CommandResult(
                request_id=request.request_id,
                status=CommandStatus.COMPLETED,
                shell=TerminalShell.WSL,
                command=request.command,
                args=request.args,
                exit_code=proc.returncode,
                stdout=stdout,
                stderr=stderr,
                duration=(end - start).total_seconds(),
                working_directory=cwd,
                timed_out=False,
                executed_at=start,
                completed_at=end,
            )

        except subprocess.TimeoutExpired:
            end = datetime.now(UTC)
            return CommandResult(
                request_id=request.request_id,
                status=CommandStatus.TIMED_OUT,
                shell=TerminalShell.WSL,
                command=request.command,
                args=request.args,
                exit_code=None,
                stdout="",
                stderr="",
                duration=(end - start).total_seconds(),
                working_directory=cwd,
                timed_out=True,
                failure_reason=CommandFailureReason.TIMEOUT,
                failure_message=f"WSL command timed out after {request.timeout}s.",
                executed_at=start,
                completed_at=end,
            )

        except Exception as exc:
            return _make_failed_result(
                request=request,
                start=start,
                reason=CommandFailureReason.PROCESS_ERROR,
                message=f"WSL execution error: {type(exc).__name__}: {exc}",
            )


def _make_failed_result(
    request: CommandRequest,
    start: datetime,
    reason: CommandFailureReason,
    message: str,
) -> CommandResult:
    now = datetime.now(UTC)
    return CommandResult(
        request_id=request.request_id,
        status=CommandStatus.FAILED,
        shell=request.shell,
        command=request.command,
        args=request.args,
        exit_code=None,
        stdout="",
        stderr="",
        duration=(now - start).total_seconds(),
        working_directory=request.working_directory,
        timed_out=False,
        failure_reason=reason,
        failure_message=message,
        executed_at=start,
        completed_at=now,
    )
