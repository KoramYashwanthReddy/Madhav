"""Unit tests for MockTerminalBackend — deterministic in-memory backend."""

import pytest

from max.terminal.backends.mock import MockTerminalBackend
from max.terminal.domain.enums import CommandStatus, TerminalShell
from max.terminal.domain.models import CommandRequest, CommandResult


@pytest.fixture
def mock_backend() -> MockTerminalBackend:
    return MockTerminalBackend()


class TestMockTerminalBackendAvailability:
    def test_is_available_by_default(self, mock_backend):
        assert mock_backend.is_available() is True

    def test_set_unavailable(self, mock_backend):
        mock_backend.set_available(False)
        assert mock_backend.is_available() is False

    def test_restore_available(self, mock_backend):
        mock_backend.set_available(False)
        mock_backend.set_available(True)
        assert mock_backend.is_available() is True


class TestMockTerminalBackendExecution:
    def test_default_execution_succeeds(self, mock_backend):
        req = CommandRequest(command="echo", args=["hello"], shell=TerminalShell.MOCK)
        result = mock_backend.execute(req)
        assert result.status == CommandStatus.COMPLETED
        assert result.exit_code == 0
        assert "echo" in result.stdout or "MOCK" in result.stdout

    def test_execution_records_are_stored(self, mock_backend):
        req = CommandRequest(command="dir", args=[], shell=TerminalShell.MOCK)
        mock_backend.execute(req)
        assert mock_backend.execution_count() == 1
        last = mock_backend.last_execution()
        assert last is not None
        assert last["command"] == "dir"

    def test_multiple_executions_recorded(self, mock_backend):
        for i in range(5):
            req = CommandRequest(command=f"cmd_{i}", args=[], shell=TerminalShell.MOCK)
            mock_backend.execute(req)
        assert mock_backend.execution_count() == 5

    def test_canned_response_returned(self, mock_backend):
        canned = CommandResult(
            request_id="test_req",
            status=CommandStatus.FAILED,
            shell=TerminalShell.MOCK,
            command="failing_cmd",
            args=[],
            exit_code=1,
            stdout="",
            stderr="simulated failure",
        )
        mock_backend.register_response("failing_cmd", canned)

        req = CommandRequest(command="failing_cmd", args=[], shell=TerminalShell.MOCK)
        result = mock_backend.execute(req)

        assert result.status == CommandStatus.FAILED
        assert result.stderr == "simulated failure"

    def test_unknown_command_gets_generic_success(self, mock_backend):
        req = CommandRequest(command="totally_unknown_cmd", args=["arg1"], shell=TerminalShell.MOCK)
        result = mock_backend.execute(req)
        assert result.status == CommandStatus.COMPLETED
        assert result.exit_code == 0

    def test_clear_responses(self, mock_backend):
        canned = CommandResult(
            request_id="r1",
            status=CommandStatus.FAILED,
            shell=TerminalShell.MOCK,
            command="some_cmd",
            args=[],
            exit_code=1,
        )
        mock_backend.register_response("some_cmd", canned)
        mock_backend.clear_responses()

        req = CommandRequest(command="some_cmd", args=[], shell=TerminalShell.MOCK)
        result = mock_backend.execute(req)
        # After clear, should get generic success not the canned response
        assert result.status == CommandStatus.COMPLETED

    def test_result_contains_request_id(self, mock_backend):
        req = CommandRequest(command="echo", args=[], shell=TerminalShell.MOCK)
        result = mock_backend.execute(req)
        assert result.request_id == req.request_id

    def test_result_command_and_args(self, mock_backend):
        req = CommandRequest(command="git", args=["status", "--short"], shell=TerminalShell.MOCK)
        result = mock_backend.execute(req)
        assert result.command == "git"
        assert result.args == ["status", "--short"]

    def test_no_subprocess_spawned(self, mock_backend):
        """Mock backend must NEVER spawn a subprocess — verified by recording only."""
        for cmd in ["rm", "sudo", "format", "runas"]:
            req = CommandRequest(command=cmd, args=[], shell=TerminalShell.MOCK)
            result = mock_backend.execute(req)
            # Mock always returns COMPLETED regardless of risk — policy is checked upstream
            assert result.status == CommandStatus.COMPLETED
        assert mock_backend.execution_count() == 4
