"""Unit tests for Module 18 CommandPolicyService — structural risk classification and policy enforcement."""

import pytest

from max.terminal.domain.enums import (
    CommandCategory,
    CommandRiskLevel,
)
from max.terminal.domain.exceptions import CommandPolicyRejectionError
from max.terminal.domain.models import CommandRequest
from max.terminal.security.command_policy import CommandPolicyService


@pytest.fixture
def policy() -> CommandPolicyService:
    return CommandPolicyService()


class TestCommandPolicyLowRisk:
    def test_echo_is_low_risk(self, policy):
        req = CommandRequest(command="echo", args=["hello"])
        clf = policy.classify(req)
        assert clf.is_allowed is True
        assert clf.risk_level == CommandRiskLevel.LOW
        assert clf.category == CommandCategory.TEXT_PROCESSING

    def test_dir_is_filesystem(self, policy):
        req = CommandRequest(command="dir", args=[])
        clf = policy.classify(req)
        assert clf.is_allowed is True
        assert clf.category == CommandCategory.FILESYSTEM

    def test_ls_is_filesystem(self, policy):
        req = CommandRequest(command="ls", args=[])
        clf = policy.classify(req)
        assert clf.is_allowed is True
        assert clf.category == CommandCategory.FILESYSTEM

    def test_grep_is_text_processing(self, policy):
        req = CommandRequest(command="grep", args=["pattern", "file.txt"])
        clf = policy.classify(req)
        assert clf.is_allowed is True
        assert clf.category == CommandCategory.TEXT_PROCESSING


class TestCommandPolicyMediumRisk:
    def test_curl_is_medium_network(self, policy):
        """curl is MEDIUM risk and classified as NETWORK — NOT auto-blocked."""
        req = CommandRequest(command="curl", args=["https://example.com"])
        clf = policy.classify(req)
        assert clf.is_allowed is True
        assert clf.risk_level == CommandRiskLevel.MEDIUM
        assert clf.category == CommandCategory.NETWORK

    def test_ping_is_medium_network(self, policy):
        req = CommandRequest(command="ping", args=["8.8.8.8"])
        clf = policy.classify(req)
        assert clf.is_allowed is True
        assert clf.risk_level == CommandRiskLevel.MEDIUM
        assert clf.category == CommandCategory.NETWORK

    def test_git_is_medium(self, policy):
        req = CommandRequest(command="git", args=["status"])
        clf = policy.classify(req)
        assert clf.is_allowed is True
        assert clf.risk_level == CommandRiskLevel.MEDIUM
        assert clf.category == CommandCategory.GIT

    def test_python_is_medium(self, policy):
        req = CommandRequest(command="python", args=["script.py"])
        clf = policy.classify(req)
        assert clf.is_allowed is True
        assert clf.risk_level == CommandRiskLevel.MEDIUM

    def test_ssh_is_medium_network(self, policy):
        req = CommandRequest(command="ssh", args=["user@host"])
        clf = policy.classify(req)
        assert clf.is_allowed is True
        assert clf.risk_level == CommandRiskLevel.MEDIUM
        assert clf.category == CommandCategory.NETWORK


class TestCommandPolicyHighRisk:
    def test_docker_is_high_risk(self, policy):
        """Docker operations must be HIGH risk."""
        req = CommandRequest(command="docker", args=["ps"])
        clf = policy.classify(req)
        assert clf.is_allowed is True
        assert clf.risk_level == CommandRiskLevel.HIGH
        assert clf.category == CommandCategory.CONTAINER

    def test_docker_run_is_high_risk(self, policy):
        req = CommandRequest(command="docker", args=["run", "-it", "ubuntu"])
        clf = policy.classify(req)
        assert clf.is_allowed is True
        assert clf.risk_level == CommandRiskLevel.HIGH

    def test_rm_is_high_risk(self, policy):
        req = CommandRequest(command="rm", args=["-rf", "/tmp/test"])
        clf = policy.classify(req)
        assert clf.is_allowed is True
        assert clf.risk_level == CommandRiskLevel.HIGH

    def test_pip_is_high_risk(self, policy):
        req = CommandRequest(command="pip", args=["install", "requests"])
        clf = policy.classify(req)
        assert clf.is_allowed is True
        assert clf.risk_level == CommandRiskLevel.HIGH

    def test_npm_is_high_risk(self, policy):
        req = CommandRequest(command="npm", args=["install"])
        clf = policy.classify(req)
        assert clf.is_allowed is True
        assert clf.risk_level == CommandRiskLevel.HIGH


class TestCommandPolicyCriticalBlocked:
    def test_runas_is_critical_blocked(self, policy):
        """runas (Windows privilege escalation) must be CRITICAL and BLOCKED."""
        req = CommandRequest(command="runas", args=["/user:Administrator", "cmd.exe"])
        clf = policy.classify(req)
        assert clf.is_allowed is False
        assert clf.risk_level == CommandRiskLevel.CRITICAL
        assert clf.category == CommandCategory.PRIVILEGE_ESCALATION
        assert clf.requires_elevated_permission is True
        assert clf.rejection_reason is not None

    def test_sudo_is_critical_blocked(self, policy):
        """sudo (Unix privilege escalation) must be CRITICAL and BLOCKED."""
        req = CommandRequest(command="sudo", args=["apt", "install", "nginx"])
        clf = policy.classify(req)
        assert clf.is_allowed is False
        assert clf.risk_level == CommandRiskLevel.CRITICAL

    def test_nested_powershell_is_critical(self, policy):
        """Launching a nested PowerShell shell is CRITICAL."""
        req = CommandRequest(command="powershell", args=["-Command", "Get-Process"])
        clf = policy.classify(req)
        assert clf.is_allowed is False
        assert clf.risk_level == CommandRiskLevel.CRITICAL

    def test_nested_cmd_is_critical(self, policy):
        req = CommandRequest(command="cmd", args=["/C", "dir"])
        clf = policy.classify(req)
        assert clf.is_allowed is False
        assert clf.risk_level == CommandRiskLevel.CRITICAL

    def test_nested_bash_is_critical(self, policy):
        req = CommandRequest(command="bash", args=["-c", "ls"])
        clf = policy.classify(req)
        assert clf.is_allowed is False
        assert clf.risk_level == CommandRiskLevel.CRITICAL

    def test_reg_is_critical(self, policy):
        req = CommandRequest(command="reg", args=["query", "HKLM"])
        clf = policy.classify(req)
        assert clf.is_allowed is False
        assert clf.risk_level == CommandRiskLevel.CRITICAL

    def test_sc_service_control_is_critical(self, policy):
        req = CommandRequest(command="sc", args=["start", "wuauserv"])
        clf = policy.classify(req)
        assert clf.is_allowed is False
        assert clf.risk_level == CommandRiskLevel.CRITICAL

    def test_wmic_is_critical(self, policy):
        req = CommandRequest(command="wmic", args=["process", "list"])
        clf = policy.classify(req)
        assert clf.is_allowed is False
        assert clf.risk_level == CommandRiskLevel.CRITICAL


class TestCommandPolicyMetacharacterRejection:
    def test_pipe_in_command_name_raises(self, policy):
        """Shell metacharacters in command name must raise CommandPolicyRejectionError."""
        req = CommandRequest(command="echo|whoami", args=[])
        with pytest.raises(CommandPolicyRejectionError):
            policy.classify(req)

    def test_semicolon_in_command_raises(self, policy):
        req = CommandRequest(command="dir;calc", args=[])
        with pytest.raises(CommandPolicyRejectionError):
            policy.classify(req)

    def test_backtick_in_command_raises(self, policy):
        req = CommandRequest(command="echo`id`", args=[])
        with pytest.raises(CommandPolicyRejectionError):
            policy.classify(req)

    def test_empty_command_raises(self, policy):
        req = CommandRequest(command="   ", args=[])
        with pytest.raises(CommandPolicyRejectionError):
            policy.classify(req)


class TestCommandPolicyWindowsExeStripping:
    def test_powershell_exe_is_critical(self, policy):
        """powershell.exe should be treated as powershell (CRITICAL nested shell)."""
        req = CommandRequest(command="powershell.exe", args=[])
        clf = policy.classify(req)
        assert clf.is_allowed is False
        assert clf.risk_level == CommandRiskLevel.CRITICAL

    def test_cmd_exe_is_critical(self, policy):
        req = CommandRequest(command="cmd.exe", args=["/C", "dir"])
        clf = policy.classify(req)
        assert clf.is_allowed is False
        assert clf.risk_level == CommandRiskLevel.CRITICAL


class TestCommandPolicyNetworkNotAutoBlocked:
    def test_nmap_allowed_medium(self, policy):
        """nmap must NOT be auto-blocked; it is classified MEDIUM/NETWORK."""
        req = CommandRequest(command="nmap", args=["-sn", "192.168.1.0/24"])
        clf = policy.classify(req)
        assert clf.is_allowed is True
        assert clf.risk_level == CommandRiskLevel.MEDIUM
        assert clf.category == CommandCategory.NETWORK

    def test_wget_allowed_medium(self, policy):
        req = CommandRequest(command="wget", args=["https://example.com/file.zip"])
        clf = policy.classify(req)
        assert clf.is_allowed is True
        assert clf.risk_level == CommandRiskLevel.MEDIUM


class TestCommandPolicyNotes:
    def test_network_command_notes_contain_advisory(self, policy):
        """Network commands must include a note saying they are not auto-blocked."""
        req = CommandRequest(command="curl", args=[])
        clf = policy.classify(req)
        assert any("not auto-blocked" in note.lower() or "network" in note.lower() for note in clf.notes)

    def test_container_command_notes_contain_review(self, policy):
        """Container commands must include a review advisory note."""
        req = CommandRequest(command="docker", args=["ps"])
        clf = policy.classify(req)
        assert any("container" in note.lower() or "high risk" in note.lower() for note in clf.notes)
