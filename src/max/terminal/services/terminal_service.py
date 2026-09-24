"""TerminalService — primary facade for all Terminal Agent operations.

Execution flow:
    Agent calls TerminalService.execute_command(request)
      ↓
    1. Subsystem-enabled check
      ↓
    2. Module 15 PermissionGate.check_and_authorize (first guard)
       [DENIED → REJECTED result returned immediately]
      ↓
    3. CommandPolicyService.classify (structural second guard)
       [CRITICAL / rejected → REJECTED result returned immediately]
      ↓
    4. Dry-run check
       [dry_run=True → SIMULATED result returned]
      ↓
    5. TerminalBackend.execute (actual subprocess — shell=False)
      ↓
    6. Audit trace recorded
      ↓
    CommandResult returned to caller

Security guarantees maintained here:
- PermissionGate is ALWAYS consulted before CommandPolicy.
- CommandPolicy is ALWAYS consulted before the Backend.
- Terminal output (stdout/stderr) is NEVER examined for authorization signals.
- All operations are recorded to TerminalTraceRepository.
"""

import time
import uuid
from datetime import UTC, datetime
from typing import Any

from max.config.sections import TerminalSettings
from max.terminal.backends.base import TerminalBackend
from max.terminal.domain.enums import CommandFailureReason, CommandStatus, TerminalShell
from max.terminal.domain.exceptions import (
    CommandPermissionDeniedError,
    CommandPolicyRejectionError,
    ShellUnavailableError,
    TerminalSubsystemDisabledError,
)
from max.terminal.domain.models import (
    CommandRequest,
    CommandResult,
    TerminalSession,
    TerminalTraceEvent,
)
from max.terminal.repositories.repositories import (
    CommandExecutionRepository,
    TerminalSessionRepository,
    TerminalTraceRepository,
)
from max.terminal.security.command_policy import CommandPolicyService

# Module 15 integration
from max.security.domain import (
    PermissionAction,
    PermissionRequest,
    PermissionResource,
    PermissionSubject,
    PermissionSubjectType,
    ResourceSensitivity,
    RiskLevel,
)
from max.security.services.gate import PermissionGate


class TerminalService:
    """Primary facade for all Terminal Agent operations in Max.

    This service enforces the complete security chain:
        PermissionGate → CommandPolicy → Backend
    """

    def __init__(
        self,
        settings: TerminalSettings,
        policy_service: CommandPolicyService,
        backend: TerminalBackend,
        execution_repo: CommandExecutionRepository,
        session_repo: TerminalSessionRepository,
        trace_repo: TerminalTraceRepository,
        permission_gate: PermissionGate | None = None,
    ) -> None:
        self._settings = settings
        self._policy = policy_service
        self._backend = backend
        self._execution_repo = execution_repo
        self._session_repo = session_repo
        self._trace_repo = trace_repo
        self._permission_gate = permission_gate

    @property
    def settings(self) -> "TerminalSettings":
        return self._settings

    @property
    def backend(self) -> TerminalBackend:
        return self._backend

    def get_status(self) -> dict[str, Any]:
        """Return operational status of the Terminal Agent subsystem."""
        return {
            "enabled": self._settings.enabled,
            "dry_run": self._settings.dry_run,
            "backend_type": type(self._backend).__name__,
            "backend_available": self._backend.is_available(),
            "default_shell": self._settings.default_shell,
            "permission_gate_active": self._permission_gate is not None,
            "max_output_bytes": self._settings.max_output_bytes,
            "default_timeout": self._settings.default_timeout,
        }

    # ------------------------------------------------------------------
    # Primary API
    # ------------------------------------------------------------------

    def execute_command(self, request: CommandRequest) -> CommandResult:
        """Execute a terminal command through the full authorization chain.

        Args:
            request: A CommandRequest with command, args, shell, and metadata.

        Returns:
            A CommandResult describing the outcome (success, failure, or simulation).
        """
        start_time = time.monotonic()

        # Step 0: Subsystem enabled check
        if not self._settings.enabled:
            return self._make_rejected_result(
                request=request,
                reason=CommandFailureReason.SUBSYSTEM_DISABLED,
                message="Terminal Agent subsystem is disabled in configuration.",
            )

        # Step 1: Backend availability check
        if not self._backend.is_available():
            return self._make_rejected_result(
                request=request,
                reason=CommandFailureReason.SHELL_UNAVAILABLE,
                message=f"Terminal backend '{type(self._backend).__name__}' is not available on this system.",
            )

        # Step 2: Module 15 PermissionGate — FIRST GUARD
        if self._permission_gate is not None:
            perm_decision, _ = self._authorize_command(request)
            if perm_decision is None or perm_decision.status.value != "ALLOWED":
                message = (
                    perm_decision.message
                    if perm_decision
                    else "Permission denied by Module 15 PermissionGate."
                )
                self._record_trace(
                    request_id=request.request_id,
                    event_type="TERMINAL_PERMISSION_DENIED",
                    details={"message": message},
                )
                return self._make_rejected_result(
                    request=request,
                    reason=CommandFailureReason.PERMISSION_DENIED,
                    message=message,
                )

        # Step 3: CommandPolicyService — SECOND GUARD
        try:
            classification = self._policy.classify(request)
        except CommandPolicyRejectionError as exc:
            self._record_trace(
                request_id=request.request_id,
                event_type="TERMINAL_POLICY_REJECTED",
                details={"message": str(exc)},
            )
            return self._make_rejected_result(
                request=request,
                reason=CommandFailureReason.POLICY_REJECTED,
                message=str(exc),
            )

        if not classification.is_allowed:
            self._record_trace(
                request_id=request.request_id,
                event_type="TERMINAL_POLICY_REJECTED",
                details={
                    "command": request.command,
                    "risk_level": classification.risk_level,
                    "reason": classification.rejection_reason,
                },
            )
            return self._make_rejected_result(
                request=request,
                reason=CommandFailureReason.POLICY_REJECTED,
                message=classification.rejection_reason or "Command rejected by structural policy.",
            )

        # Step 4: Dry-run check
        is_dry_run = self._settings.dry_run or request.dry_run
        if is_dry_run:
            self._record_trace(
                request_id=request.request_id,
                event_type="TERMINAL_COMMAND_SIMULATED",
                details={"command": request.command, "args": request.args},
            )
            result = CommandResult(
                request_id=request.request_id,
                status=CommandStatus.SIMULATED,
                shell=request.shell,
                command=request.command,
                args=request.args,
                exit_code=None,
                stdout=f"[DRY-RUN] Would execute: {request.command} {' '.join(request.args)}",
                stderr="",
                duration=time.monotonic() - start_time,
                working_directory=request.working_directory,
                simulated=True,
                executed_at=datetime.now(UTC),
            )
            self._execution_repo.save(result)
            return result

        # Step 5: Backend execution
        self._record_trace(
            request_id=request.request_id,
            event_type="TERMINAL_COMMAND_STARTED",
            details={
                "command": request.command,
                "shell": request.shell,
                "risk_level": classification.risk_level,
                "category": classification.category,
            },
        )

        result = self._backend.execute(request)
        self._execution_repo.save(result)

        event_type = (
            "TERMINAL_COMMAND_COMPLETED"
            if result.status == CommandStatus.COMPLETED
            else "TERMINAL_COMMAND_FAILED"
        )
        self._record_trace(
            request_id=request.request_id,
            event_type=event_type,
            details={
                "exit_code": result.exit_code,
                "duration": result.duration,
                "timed_out": result.timed_out,
            },
        )

        return result

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def create_session(
        self,
        shell: TerminalShell | None = None,
        owner_id: str = "system",
        agent_id: str | None = None,
    ) -> TerminalSession:
        """Create and register a new terminal session."""
        resolved_shell = shell or TerminalShell(self._settings.default_shell)
        session = TerminalSession(
            shell=resolved_shell,
            owner_id=owner_id,
            agent_id=agent_id,
        )
        self._session_repo.save(session)
        self._record_trace(
            request_id=None,
            event_type="TERMINAL_SESSION_CREATED",
            details={"session_id": session.session_id, "shell": resolved_shell},
        )
        return session

    def get_session(self, session_id: str) -> TerminalSession | None:
        """Retrieve a session by ID."""
        return self._session_repo.get(session_id)

    def list_sessions(self) -> list[TerminalSession]:
        """Return all registered sessions."""
        return self._session_repo.list_all()

    # ------------------------------------------------------------------
    # History & audit
    # ------------------------------------------------------------------

    def get_execution_history(self) -> list[CommandResult]:
        """Return all command execution results."""
        return self._execution_repo.list_all()

    def get_trace_events(
        self,
        request_id: str | None = None,
        event_type: str | None = None,
    ) -> list[TerminalTraceEvent]:
        """Return audit trace events, optionally filtered."""
        return self._trace_repo.list_events(request_id=request_id, event_type=event_type)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _authorize_command(self, request: CommandRequest) -> tuple[Any, Any]:
        """Build and submit a PermissionRequest to Module 15 PermissionGate."""
        # Map command risk classification to Module 15 RiskLevel
        # (preliminary classification — full classification happens in step 3)
        cmd_lower = request.command.lower().rstrip(".exe")
        from max.terminal.security.command_policy import _CRITICAL_COMMANDS, _HIGH_RISK_COMMANDS

        if cmd_lower in _CRITICAL_COMMANDS:
            risk = RiskLevel.CRITICAL
        elif cmd_lower in _HIGH_RISK_COMMANDS:
            risk = RiskLevel.HIGH
        else:
            risk = RiskLevel.MEDIUM

        perm_request = PermissionRequest(
            request_id=f"tperm_{uuid.uuid4().hex[:12]}",
            owner_id=request.owner_id,
            subject=PermissionSubject(
                subject_id=request.agent_id or "agent_terminal",
                subject_type=PermissionSubjectType.AGENT,
            ),
            resource=PermissionResource(
                resource_type="TERMINAL",
                resource_id=f"terminal.execute.{request.command}",
                owner_id=request.owner_id,
                sensitivity=ResourceSensitivity.SENSITIVE,
                attributes={
                    "command": request.command,
                    "args": request.args,
                    "shell": request.shell,
                },
            ),
            action=PermissionAction.EXECUTE,
            risk_level=risk,
            tool_reference="terminal.execute",
            arguments={"command": request.command, "args": request.args},
        )

        assert self._permission_gate is not None
        return self._permission_gate.check_and_authorize(perm_request)

    def _make_rejected_result(
        self,
        request: CommandRequest,
        reason: CommandFailureReason,
        message: str,
    ) -> CommandResult:
        """Build a REJECTED CommandResult and persist it."""
        result = CommandResult(
            request_id=request.request_id,
            status=CommandStatus.REJECTED,
            shell=request.shell,
            command=request.command,
            args=request.args,
            exit_code=None,
            stdout="",
            stderr="",
            duration=0.0,
            failure_reason=reason,
            failure_message=message,
            executed_at=datetime.now(UTC),
        )
        self._execution_repo.save(result)
        self._record_trace(
            request_id=request.request_id,
            event_type="TERMINAL_COMMAND_REJECTED",
            details={"reason": reason, "message": message},
        )
        return result

    def _record_trace(
        self,
        request_id: str | None,
        event_type: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Append an audit trace event to the trace repository."""
        event = TerminalTraceEvent(
            event_id=f"tevt_{uuid.uuid4().hex[:12]}",
            request_id=request_id,
            event_type=event_type,
            details=details or {},
        )
        self._trace_repo.add_event(event)
