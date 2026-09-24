"""Deterministic in-memory MockTerminalBackend for safe testing.

The mock never spawns any processes.  It records all invocations and
returns preconfigured canned responses or generic success results.

Used in:
- All unit tests
- Dry-run smoke tests during development
- CI environments where no shell is available
"""

import threading
from datetime import UTC, datetime
from typing import Any

from max.terminal.backends.base import TerminalBackend
from max.terminal.domain.enums import CommandFailureReason, CommandStatus, TerminalShell
from max.terminal.domain.models import CommandRequest, CommandResult


class MockTerminalBackend(TerminalBackend):
    """Deterministic mock terminal backend for testing and simulation.

    Supports pre-registration of per-command responses via ``register_response``.
    Commands not explicitly registered return a generic success result with
    simulated stdout containing the command echo.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.recorded_executions: list[dict[str, Any]] = []
        self._responses: dict[str, CommandResult] = {}
        self._available: bool = True

    def set_available(self, available: bool) -> None:
        """Toggle mock backend availability (for testing unavailable shell scenarios)."""
        with self._lock:
            self._available = available

    def register_response(self, command: str, result: CommandResult) -> None:
        """Pre-register a canned result to be returned for a specific command name."""
        with self._lock:
            self._responses[command] = result

    def clear_responses(self) -> None:
        """Clear all pre-registered canned responses."""
        with self._lock:
            self._responses.clear()

    def is_available(self) -> bool:
        return self._available

    def execute(self, request: CommandRequest) -> CommandResult:
        """Execute a mock command — no subprocess spawned, fully deterministic."""
        start = datetime.now(UTC)

        with self._lock:
            self.recorded_executions.append(
                {
                    "request_id": request.request_id,
                    "command": request.command,
                    "args": request.args,
                    "shell": request.shell,
                    "working_directory": request.working_directory,
                    "dry_run": request.dry_run,
                    "timestamp": start.isoformat(),
                }
            )

            # Return canned response if registered
            if request.command in self._responses:
                return self._responses[request.command]

            # Default: simulate successful execution
            end = datetime.now(UTC)
            cmd_str = " ".join([request.command] + request.args)
            return CommandResult(
                request_id=request.request_id,
                status=CommandStatus.COMPLETED,
                shell=request.shell if request.shell != TerminalShell.MOCK else TerminalShell.MOCK,
                command=request.command,
                args=request.args,
                exit_code=0,
                stdout=f"[MOCK] Executed: {cmd_str}",
                stderr="",
                duration=(end - start).total_seconds(),
                working_directory=request.working_directory,
                timed_out=False,
                executed_at=start,
                completed_at=end,
            )

    def last_execution(self) -> dict[str, Any] | None:
        """Return the most recently recorded execution dict, or None."""
        with self._lock:
            return self.recorded_executions[-1] if self.recorded_executions else None

    def execution_count(self) -> int:
        """Return the total number of executions recorded so far."""
        with self._lock:
            return len(self.recorded_executions)
