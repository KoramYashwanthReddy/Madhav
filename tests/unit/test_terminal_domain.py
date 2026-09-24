"""Unit tests for Module 18 Terminal Agent domain models and enums."""

import pytest

from max.terminal.domain.enums import (
    CommandCategory,
    CommandFailureReason,
    CommandRiskLevel,
    CommandStatus,
    SessionStatus,
    TerminalShell,
)
from max.terminal.domain.exceptions import (
    CommandPermissionDeniedError,
    CommandPolicyRejectionError,
    CommandTimeoutError,
    InvalidCommandError,
    PromptInjectionDefenseError,
    ShellUnavailableError,
    TerminalError,
    TerminalSubsystemDisabledError,
    WorkingDirectoryViolationError,
)
from max.terminal.domain.models import (
    CommandClassification,
    CommandRequest,
    CommandResult,
    TerminalSession,
    TerminalTraceEvent,
)


class TestTerminalDomainEnums:
    def test_terminal_shell_values(self):
        assert TerminalShell.POWERSHELL == "POWERSHELL"
        assert TerminalShell.CMD == "CMD"
        assert TerminalShell.WSL == "WSL"
        assert TerminalShell.MOCK == "MOCK"

    def test_command_risk_level_values(self):
        assert CommandRiskLevel.LOW == "LOW"
        assert CommandRiskLevel.MEDIUM == "MEDIUM"
        assert CommandRiskLevel.HIGH == "HIGH"
        assert CommandRiskLevel.CRITICAL == "CRITICAL"

    def test_command_status_values(self):
        assert CommandStatus.CREATED == "CREATED"
        assert CommandStatus.COMPLETED == "COMPLETED"
        assert CommandStatus.REJECTED == "REJECTED"
        assert CommandStatus.SIMULATED == "SIMULATED"
        assert CommandStatus.TIMED_OUT == "TIMED_OUT"
        assert CommandStatus.FAILED == "FAILED"

    def test_command_failure_reason_values(self):
        assert CommandFailureReason.PERMISSION_DENIED == "PERMISSION_DENIED"
        assert CommandFailureReason.POLICY_REJECTED == "POLICY_REJECTED"
        assert CommandFailureReason.TIMEOUT == "TIMEOUT"
        assert CommandFailureReason.SUBSYSTEM_DISABLED == "SUBSYSTEM_DISABLED"

    def test_session_status_values(self):
        assert SessionStatus.ACTIVE == "ACTIVE"
        assert SessionStatus.CLOSED == "CLOSED"
        assert SessionStatus.EXPIRED == "EXPIRED"

    def test_command_category_values(self):
        assert CommandCategory.NETWORK == "NETWORK"
        assert CommandCategory.PRIVILEGE_ESCALATION == "PRIVILEGE_ESCALATION"
        assert CommandCategory.CONTAINER == "CONTAINER"
        assert CommandCategory.FILESYSTEM == "FILESYSTEM"


class TestTerminalDomainExceptions:
    def test_exception_hierarchy(self):
        for exc_cls in [
            TerminalSubsystemDisabledError,
            CommandPolicyRejectionError,
            CommandPermissionDeniedError,
            InvalidCommandError,
            WorkingDirectoryViolationError,
            ShellUnavailableError,
            CommandTimeoutError,
            PromptInjectionDefenseError,
        ]:
            assert issubclass(exc_cls, TerminalError)

    def test_exceptions_are_raiseable(self):
        with pytest.raises(CommandPolicyRejectionError):
            raise CommandPolicyRejectionError("blocked by policy")

        with pytest.raises(PromptInjectionDefenseError):
            raise PromptInjectionDefenseError("prompt injection detected")


class TestCommandRequest:
    def test_default_construction(self):
        req = CommandRequest(command="echo")
        assert req.command == "echo"
        assert req.args == []
        assert req.shell == TerminalShell.POWERSHELL
        assert req.timeout == 30.0
        assert req.dry_run is False
        assert req.request_id.startswith("cmd_")

    def test_custom_construction(self):
        req = CommandRequest(
            command="git",
            args=["status"],
            shell=TerminalShell.CMD,
            timeout=10.0,
            owner_id="user_1",
            agent_id="agent_42",
        )
        assert req.args == ["status"]
        assert req.shell == TerminalShell.CMD
        assert req.timeout == 10.0
        assert req.owner_id == "user_1"
        assert req.agent_id == "agent_42"

    def test_request_id_uniqueness(self):
        ids = {CommandRequest(command="echo").request_id for _ in range(20)}
        assert len(ids) == 20


class TestCommandResult:
    def test_completed_result(self):
        req = CommandRequest(command="echo", args=["hello"])
        result = CommandResult(
            request_id=req.request_id,
            status=CommandStatus.COMPLETED,
            shell=TerminalShell.POWERSHELL,
            command="echo",
            args=["hello"],
            exit_code=0,
            stdout="hello",
            stderr="",
            duration=0.1,
        )
        assert result.status == CommandStatus.COMPLETED
        assert result.exit_code == 0
        assert result.stdout == "hello"
        assert result.timed_out is False
        assert result.simulated is False

    def test_rejected_result(self):
        req = CommandRequest(command="sudo")
        result = CommandResult(
            request_id=req.request_id,
            status=CommandStatus.REJECTED,
            shell=TerminalShell.POWERSHELL,
            command="sudo",
            args=[],
            failure_reason=CommandFailureReason.POLICY_REJECTED,
            failure_message="sudo is CRITICAL",
        )
        assert result.status == CommandStatus.REJECTED
        assert result.failure_reason == CommandFailureReason.POLICY_REJECTED
        assert result.exit_code is None

    def test_simulated_result(self):
        req = CommandRequest(command="dir", dry_run=True)
        result = CommandResult(
            request_id=req.request_id,
            status=CommandStatus.SIMULATED,
            shell=TerminalShell.POWERSHELL,
            command="dir",
            args=[],
            simulated=True,
        )
        assert result.simulated is True
        assert result.status == CommandStatus.SIMULATED


class TestTerminalSession:
    def test_default_session(self):
        session = TerminalSession(shell=TerminalShell.POWERSHELL)
        assert session.shell == TerminalShell.POWERSHELL
        assert session.status == SessionStatus.ACTIVE
        assert session.command_count == 0
        assert session.session_id.startswith("sess_")

    def test_session_id_uniqueness(self):
        ids = {TerminalSession(shell=TerminalShell.POWERSHELL).session_id for _ in range(20)}
        assert len(ids) == 20


class TestCommandClassification:
    def test_allowed_low_risk(self):
        clf = CommandClassification(
            command="echo",
            args=["hello"],
            category=CommandCategory.TEXT_PROCESSING,
            risk_level=CommandRiskLevel.LOW,
            is_allowed=True,
        )
        assert clf.is_allowed is True
        assert clf.rejection_reason is None
        assert clf.requires_elevated_permission is False

    def test_rejected_critical(self):
        clf = CommandClassification(
            command="sudo",
            args=[],
            category=CommandCategory.PRIVILEGE_ESCALATION,
            risk_level=CommandRiskLevel.CRITICAL,
            is_allowed=False,
            rejection_reason="sudo is CRITICAL",
            requires_elevated_permission=True,
        )
        assert clf.is_allowed is False
        assert clf.rejection_reason is not None
        assert clf.requires_elevated_permission is True


class TestTerminalTraceEvent:
    def test_trace_event_creation(self):
        evt = TerminalTraceEvent(
            event_type="TERMINAL_COMMAND_STARTED",
            request_id="cmd_abc123",
            details={"command": "echo"},
        )
        assert evt.event_type == "TERMINAL_COMMAND_STARTED"
        assert evt.event_id.startswith("tevt_")
        assert evt.details["command"] == "echo"

    def test_trace_event_id_uniqueness(self):
        ids = {TerminalTraceEvent(event_type="TEST").event_id for _ in range(20)}
        assert len(ids) == 20
