"""Unit tests for Module 18 TerminalService facade with MockTerminalBackend.

Tests the complete security chain:
    enabled check → PermissionGate → CommandPolicy → dry_run → backend
"""

import pytest

from max.config.sections import TerminalSettings
from max.terminal.backends.mock import MockTerminalBackend
from max.terminal.domain.enums import CommandFailureReason, CommandStatus, TerminalShell
from max.terminal.domain.models import CommandRequest
from max.terminal.repositories.repositories import (
    CommandExecutionRepository,
    TerminalSessionRepository,
    TerminalTraceRepository,
)
from max.terminal.security.command_policy import CommandPolicyService
from max.terminal.services.terminal_service import TerminalService


@pytest.fixture
def service_setup():
    """Build a TerminalService with MockBackend and no PermissionGate (pure policy tests)."""
    settings = TerminalSettings(
        enabled=True,
        dry_run=False,
        default_shell="MOCK",
    )
    backend = MockTerminalBackend()
    policy = CommandPolicyService()
    execution_repo = CommandExecutionRepository()
    session_repo = TerminalSessionRepository()
    trace_repo = TerminalTraceRepository()

    service = TerminalService(
        settings=settings,
        policy_service=policy,
        backend=backend,
        execution_repo=execution_repo,
        session_repo=session_repo,
        trace_repo=trace_repo,
        permission_gate=None,  # Disabled for pure unit tests
    )
    return service, backend, execution_repo, trace_repo


class TestTerminalServiceStatus:
    def test_get_status_structure(self, service_setup):
        service, _, _, _ = service_setup
        status = service.get_status()
        assert status["enabled"] is True
        assert status["dry_run"] is False
        assert "backend_type" in status
        assert "permission_gate_active" in status
        assert status["permission_gate_active"] is False


class TestTerminalServiceLowRiskExecution:
    def test_echo_command_executes(self, service_setup):
        service, backend, execution_repo, _ = service_setup
        req = CommandRequest(command="echo", args=["hello"], shell=TerminalShell.MOCK)
        result = service.execute_command(req)
        assert result.status == CommandStatus.COMPLETED
        assert result.exit_code == 0
        assert backend.execution_count() == 1

    def test_dir_command_executes(self, service_setup):
        service, _, _, _ = service_setup
        req = CommandRequest(command="dir", args=[], shell=TerminalShell.MOCK)
        result = service.execute_command(req)
        assert result.status == CommandStatus.COMPLETED

    def test_execution_recorded_in_repository(self, service_setup):
        service, _, execution_repo, _ = service_setup
        req = CommandRequest(command="ls", args=["-la"], shell=TerminalShell.MOCK)
        result = service.execute_command(req)
        assert result.status == CommandStatus.COMPLETED
        stored = execution_repo.get(req.request_id)
        assert stored is not None
        assert stored.status == CommandStatus.COMPLETED

    def test_trace_events_recorded(self, service_setup):
        service, _, _, trace_repo = service_setup
        req = CommandRequest(command="echo", args=["test"], shell=TerminalShell.MOCK)
        service.execute_command(req)
        events = trace_repo.list_events(request_id=req.request_id)
        assert len(events) >= 1
        event_types = [e.event_type for e in events]
        assert "TERMINAL_COMMAND_STARTED" in event_types
        assert "TERMINAL_COMMAND_COMPLETED" in event_types


class TestTerminalServiceNetworkCommands:
    def test_curl_is_allowed_and_executes(self, service_setup):
        """curl must be ALLOWED (MEDIUM risk network) — not auto-blocked."""
        service, _, _, _ = service_setup
        req = CommandRequest(command="curl", args=["https://example.com"], shell=TerminalShell.MOCK)
        result = service.execute_command(req)
        assert result.status == CommandStatus.COMPLETED

    def test_ping_is_allowed(self, service_setup):
        service, _, _, _ = service_setup
        req = CommandRequest(command="ping", args=["8.8.8.8"], shell=TerminalShell.MOCK)
        result = service.execute_command(req)
        assert result.status == CommandStatus.COMPLETED

    def test_ssh_is_allowed_medium_risk(self, service_setup):
        service, _, _, _ = service_setup
        req = CommandRequest(command="ssh", args=["user@host"], shell=TerminalShell.MOCK)
        result = service.execute_command(req)
        assert result.status == CommandStatus.COMPLETED


class TestTerminalServiceCriticalBlocked:
    def test_sudo_rejected_by_policy(self, service_setup):
        """sudo must be REJECTED by CommandPolicyService as CRITICAL."""
        service, backend, _, trace_repo = service_setup
        req = CommandRequest(command="sudo", args=["rm", "-rf", "/"], shell=TerminalShell.MOCK)
        result = service.execute_command(req)
        # Must be REJECTED — no backend execution should occur
        assert result.status == CommandStatus.REJECTED
        assert result.failure_reason == CommandFailureReason.POLICY_REJECTED
        assert backend.execution_count() == 0  # Backend must NOT be called

    def test_runas_rejected_by_policy(self, service_setup):
        service, backend, _, _ = service_setup
        req = CommandRequest(command="runas", args=["/user:Administrator", "cmd.exe"], shell=TerminalShell.MOCK)
        result = service.execute_command(req)
        assert result.status == CommandStatus.REJECTED
        assert result.failure_reason == CommandFailureReason.POLICY_REJECTED
        assert backend.execution_count() == 0

    def test_nested_powershell_rejected(self, service_setup):
        service, backend, _, _ = service_setup
        req = CommandRequest(command="powershell.exe", args=["-Command", "Get-Process"], shell=TerminalShell.MOCK)
        result = service.execute_command(req)
        assert result.status == CommandStatus.REJECTED
        assert backend.execution_count() == 0

    def test_nested_cmd_rejected(self, service_setup):
        service, backend, _, _ = service_setup
        req = CommandRequest(command="cmd", args=["/C", "dir"], shell=TerminalShell.MOCK)
        result = service.execute_command(req)
        assert result.status == CommandStatus.REJECTED
        assert backend.execution_count() == 0

    def test_reg_rejected_by_policy(self, service_setup):
        service, backend, _, _ = service_setup
        req = CommandRequest(command="reg", args=["add", "HKLM\\Software\\Test"], shell=TerminalShell.MOCK)
        result = service.execute_command(req)
        assert result.status == CommandStatus.REJECTED
        assert backend.execution_count() == 0

    def test_rejected_command_stored_in_repository(self, service_setup):
        service, _, execution_repo, _ = service_setup
        req = CommandRequest(command="sudo", args=[], shell=TerminalShell.MOCK)
        service.execute_command(req)
        stored = execution_repo.get(req.request_id)
        assert stored is not None
        assert stored.status == CommandStatus.REJECTED


class TestTerminalServiceSubsystemDisabled:
    def test_disabled_subsystem_rejects_all(self, service_setup):
        service, backend, _, _ = service_setup
        service._settings.enabled = False
        req = CommandRequest(command="echo", args=["hi"], shell=TerminalShell.MOCK)
        result = service.execute_command(req)
        assert result.status == CommandStatus.REJECTED
        assert result.failure_reason == CommandFailureReason.SUBSYSTEM_DISABLED
        assert backend.execution_count() == 0


class TestTerminalServiceDryRun:
    def test_dry_run_flag_on_request(self, service_setup):
        service, backend, _, _ = service_setup
        req = CommandRequest(command="echo", args=["hello"], shell=TerminalShell.MOCK, dry_run=True)
        result = service.execute_command(req)
        assert result.status == CommandStatus.SIMULATED
        assert result.simulated is True
        assert backend.execution_count() == 0  # No actual execution

    def test_global_dry_run_setting(self, service_setup):
        service, backend, _, _ = service_setup
        service._settings.dry_run = True
        req = CommandRequest(command="dir", args=[], shell=TerminalShell.MOCK)
        result = service.execute_command(req)
        assert result.status == CommandStatus.SIMULATED
        assert backend.execution_count() == 0

    def test_dry_run_still_rejects_critical(self, service_setup):
        """Even in dry-run, CRITICAL commands must be rejected before reaching dry-run check."""
        service, backend, _, _ = service_setup
        req = CommandRequest(command="sudo", args=[], shell=TerminalShell.MOCK, dry_run=True)
        result = service.execute_command(req)
        # Policy check happens before dry-run check → must be REJECTED not SIMULATED
        assert result.status == CommandStatus.REJECTED
        assert result.failure_reason == CommandFailureReason.POLICY_REJECTED


class TestTerminalServiceUnavailableBackend:
    def test_unavailable_backend_rejected(self, service_setup):
        service, backend, _, _ = service_setup
        backend.set_available(False)
        req = CommandRequest(command="echo", args=[], shell=TerminalShell.MOCK)
        result = service.execute_command(req)
        assert result.status == CommandStatus.REJECTED
        assert result.failure_reason == CommandFailureReason.SHELL_UNAVAILABLE


class TestTerminalServiceMetacharacterRejection:
    def test_metacharacter_in_command_rejected(self, service_setup):
        service, backend, _, _ = service_setup
        req = CommandRequest(command="echo|whoami", args=[], shell=TerminalShell.MOCK)
        result = service.execute_command(req)
        assert result.status == CommandStatus.REJECTED
        assert result.failure_reason == CommandFailureReason.POLICY_REJECTED
        assert backend.execution_count() == 0


class TestTerminalServiceSessions:
    def test_create_session(self, service_setup):
        service, _, _, _ = service_setup
        session = service.create_session(shell=TerminalShell.POWERSHELL, owner_id="user_1")
        assert session.session_id.startswith("sess_")
        assert session.shell == TerminalShell.POWERSHELL

    def test_get_session_by_id(self, service_setup):
        service, _, _, _ = service_setup
        session = service.create_session(shell=TerminalShell.CMD)
        retrieved = service.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.session_id == session.session_id

    def test_get_nonexistent_session_returns_none(self, service_setup):
        service, _, _, _ = service_setup
        assert service.get_session("nonexistent_session_id") is None

    def test_list_sessions(self, service_setup):
        service, _, _, _ = service_setup
        service.create_session(shell=TerminalShell.POWERSHELL)
        service.create_session(shell=TerminalShell.CMD)
        sessions = service.list_sessions()
        assert len(sessions) == 2


class TestTerminalServiceHistory:
    def test_execution_history_empty_initially(self, service_setup):
        service, _, _, _ = service_setup
        history = service.get_execution_history()
        assert history == []

    def test_execution_history_populated_after_run(self, service_setup):
        service, _, _, _ = service_setup
        req = CommandRequest(command="echo", args=["a"], shell=TerminalShell.MOCK)
        service.execute_command(req)
        history = service.get_execution_history()
        assert len(history) == 1
        assert history[0].command == "echo"

    def test_trace_events_accessible(self, service_setup):
        service, _, _, trace_repo = service_setup
        req = CommandRequest(command="dir", args=[], shell=TerminalShell.MOCK)
        service.execute_command(req)
        events = service.get_trace_events(request_id=req.request_id)
        assert len(events) >= 1
