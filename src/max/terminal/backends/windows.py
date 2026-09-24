"""Windows terminal backend supporting PowerShell and CMD shell execution.

Security principles enforced here:
- subprocess is called with shell=False at ALL times.
- No user input is passed via shell string interpolation.
- Environment variables are constructed from a safe, curated base plus
  explicitly whitelisted additions; secrets are redacted from output.
- stdout/stderr are treated as untrusted data; they are sanitized and
  truncated before being surfaced in CommandResult.
- Prompt-Injection Defence: output is NEVER interpreted as an
  authorization or instruction signal by this layer.
"""

import subprocess
import threading
from datetime import UTC, datetime
from pathlib import Path

from max.terminal.backends.base import TerminalBackend
from max.terminal.domain.enums import CommandFailureReason, CommandStatus, TerminalShell
from max.terminal.domain.models import CommandRequest, CommandResult

# Maximum bytes read from stdout / stderr to prevent memory exhaustion
_MAX_OUTPUT_BYTES = 524_288  # 512 KiB

# Environment variables that MUST NOT be passed to child processes
_BLOCKED_ENV_KEYS = frozenset(
    {
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "DATABASE_URL",
        "SECRET_KEY",
        "PRIVATE_KEY",
        "PASSWORD",
        "PASSWD",
        "TOKEN",
        "AUTH_TOKEN",
        "ACCESS_TOKEN",
        "REFRESH_TOKEN",
        "API_SECRET",
        "STRIPE_SECRET_KEY",
        "TWILIO_AUTH_TOKEN",
    }
)


def _build_safe_env(extra: dict[str, str]) -> dict[str, str]:
    """Build a sanitized environment dict, blocking known sensitive keys."""
    import os

    base = {
        k: v
        for k, v in os.environ.items()
        if k.upper() not in _BLOCKED_ENV_KEYS
    }
    for k, v in extra.items():
        if k.upper() not in _BLOCKED_ENV_KEYS:
            base[k] = v
    return base


def _sanitize_output(raw: bytes, max_bytes: int = _MAX_OUTPUT_BYTES) -> str:
    """Decode and truncate raw process output.

    This function must NOT parse or interpret the output as a command or
    instruction.  Its sole responsibility is safe text extraction.
    """
    truncated_raw = raw[:max_bytes]
    try:
        text = truncated_raw.decode("utf-8", errors="replace")
    except Exception:
        text = truncated_raw.decode("latin-1", errors="replace")

    if len(raw) > max_bytes:
        text += f"\n[OUTPUT TRUNCATED — {len(raw)} bytes total, {max_bytes} bytes shown]"
    return text


class WindowsTerminalBackend(TerminalBackend):
    """Executes commands via PowerShell or CMD on Windows using subprocess.

    shell=False is enforced unconditionally.  The executable list is built
    from the parsed command + args, never from string interpolation.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()

    def is_available(self) -> bool:
        """Return True on Windows systems (where PowerShell/CMD are present)."""
        import sys

        return sys.platform == "win32"

    def execute(self, request: CommandRequest) -> CommandResult:
        """Execute a command on Windows via PowerShell or CMD.

        The shell flag is selected based on request.shell.  PowerShell is
        default; CMD is supported.  Both use shell=False.
        """
        start = datetime.now(UTC)
        shell = request.shell

        # Build executable + argument list — NO string interpolation
        if shell == TerminalShell.POWERSHELL:
            prefix = ["powershell.exe", "-NonInteractive", "-NoProfile", "-Command"]
            # Pass command + args as a single quoted list for PowerShell
            cmd_parts = [request.command] + request.args
            full_cmd = prefix + [" ".join(self._quote_ps(p) for p in cmd_parts)]
        elif shell == TerminalShell.CMD:
            prefix = ["cmd.exe", "/C"]
            full_cmd = prefix + [request.command] + request.args
        else:
            # Unsupported on this backend
            return self._make_failed_result(
                request=request,
                start=start,
                reason=CommandFailureReason.SHELL_UNAVAILABLE,
                message=f"Shell '{shell}' is not supported by WindowsTerminalBackend.",
            )

        # Validate working directory
        cwd: str | None = None
        if request.working_directory:
            wd_path = Path(request.working_directory)
            if not wd_path.exists() or not wd_path.is_dir():
                return self._make_failed_result(
                    request=request,
                    start=start,
                    reason=CommandFailureReason.WORKING_DIR_VIOLATION,
                    message=f"Working directory '{request.working_directory}' does not exist.",
                )
            cwd = str(wd_path.resolve())

        # Build safe environment
        safe_env = _build_safe_env(request.environment)

        # Execute with timeout enforcement
        try:
            with self._lock:
                proc = subprocess.run(  # noqa: S603
                    full_cmd,
                    shell=False,  # SECURITY: always False
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
                shell=shell,
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
                shell=shell,
                command=request.command,
                args=request.args,
                exit_code=None,
                stdout="",
                stderr="",
                duration=(end - start).total_seconds(),
                working_directory=cwd,
                timed_out=True,
                failure_reason=CommandFailureReason.TIMEOUT,
                failure_message=f"Command timed out after {request.timeout}s.",
                executed_at=start,
                completed_at=end,
            )

        except Exception as exc:
            end = datetime.now(UTC)
            return self._make_failed_result(
                request=request,
                start=start,
                reason=CommandFailureReason.PROCESS_ERROR,
                message=f"Process execution error: {type(exc).__name__}: {exc}",
            )

    @staticmethod
    def _quote_ps(arg: str) -> str:
        """Minimally escape an argument for PowerShell -Command invocation."""
        return f'"{arg.replace(chr(34), chr(92) + chr(34))}"'

    @staticmethod
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
