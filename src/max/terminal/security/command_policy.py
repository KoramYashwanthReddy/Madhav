"""CommandPolicyService — second line of defense for terminal command authorization.

Architecture:
    Agent
      ↓
    TerminalService  ←  calls Module 15 PermissionGate (first check)
      ↓ (ALLOWED)
    CommandPolicyService  ←  THIS FILE (second check, structural policy)
      ↓ (ALLOWED)
    TerminalBackend  ←  actual subprocess execution

Responsibilities:
- Classify commands by risk level (LOW / MEDIUM / HIGH / CRITICAL).
- Evaluate structural policy rules (blocked prefixes, privilege escalation
  detection, docker, network command classification).
- Reject commands that fail policy WITHOUT ever executing them.
- Never interpret command output as a signal (prompt-injection defence).

User requirements:
- Do NOT automatically block all networking; classify appropriately.
- Docker operations are HIGH risk.
- Privilege escalation (runas, sudo) is CRITICAL.
- Terminal output must NEVER be interpreted as authorization.
"""

from max.terminal.domain.enums import CommandCategory, CommandRiskLevel
from max.terminal.domain.exceptions import CommandPolicyRejectionError
from max.terminal.domain.models import CommandClassification, CommandRequest

# ---------------------------------------------------------------------------
# Policy tables
# ---------------------------------------------------------------------------

# Commands classified as CRITICAL — require explicit user grant
_CRITICAL_COMMANDS = frozenset(
    {
        "runas",       # Windows privilege escalation
        "sudo",        # Unix privilege escalation
        "su",          # Unix privilege escalation
        "net",         # Windows user/service management (net user, net localgroup …)
        "netsh",       # Windows network stack configuration
        "reg",         # Windows registry editor
        "regedit",     # Windows registry GUI
        "bcdedit",     # Boot configuration
        "diskpart",    # Disk partitioning
        "format",      # Disk formatting
        "cipher",      # EFS encryption (can wipe)
        "takeown",     # Ownership takeover
        "icacls",      # ACL modification
        "cacls",       # Legacy ACL tool
        "attrib",      # Hidden/system attribute manipulation
        "sc",          # Windows service control
        "schtasks",    # Scheduled task creation/modification
        "wmic",        # WMI — broad system interrogation/modification
        "powershell",  # Nested shell launch
        "cmd",         # Nested CMD launch
        "bash",        # Nested bash launch
        "sh",          # Nested sh launch
        "zsh",         # Nested zsh launch
    }
)

# Commands classified as HIGH risk — allowed with HIGH permission grant
_HIGH_RISK_COMMANDS = frozenset(
    {
        # Container / virtualization
        "docker",
        "docker-compose",
        "podman",
        "kubectl",
        "helm",
        # Process management
        "taskkill",
        "kill",
        "pkill",
        "killall",
        # System state
        "shutdown",
        "reboot",
        "restart",
        "halt",
        "poweroff",
        # File system (potentially destructive)
        "rm",
        "rmdir",
        "del",
        "rd",
        # Potentially wide-net installers
        "choco",
        "winget",
        "apt",
        "apt-get",
        "yum",
        "dnf",
        "pacman",
        "brew",
        "pip",
        "pip3",
        "npm",
        "yarn",
        "cargo",
    }
)

# Commands classified as MEDIUM risk — allowed by default with MEDIUM grant
_MEDIUM_RISK_COMMANDS = frozenset(
    {
        # Network observation (read-only)
        "curl",
        "wget",
        "ping",
        "tracert",
        "traceroute",
        "nslookup",
        "dig",
        "nmap",
        "ssh",
        "scp",
        "sftp",
        "rsync",
        "ftp",
        "telnet",
        # Git (write ops)
        "git",
        # Process inspection
        "tasklist",
        "ps",
        "top",
        "htop",
        # Env inspection
        "env",
        "set",
        "printenv",
        # Execution
        "python",
        "python3",
        "node",
        "ruby",
        "java",
    }
)

# Category mappings
_CATEGORY_MAP: dict[str, CommandCategory] = {
    # Network
    "curl": CommandCategory.NETWORK,
    "wget": CommandCategory.NETWORK,
    "ping": CommandCategory.NETWORK,
    "tracert": CommandCategory.NETWORK,
    "traceroute": CommandCategory.NETWORK,
    "nslookup": CommandCategory.NETWORK,
    "dig": CommandCategory.NETWORK,
    "nmap": CommandCategory.NETWORK,
    "ssh": CommandCategory.NETWORK,
    "scp": CommandCategory.NETWORK,
    "sftp": CommandCategory.NETWORK,
    "rsync": CommandCategory.NETWORK,
    "ftp": CommandCategory.NETWORK,
    "telnet": CommandCategory.NETWORK,
    "netsh": CommandCategory.NETWORK,
    # System admin
    "net": CommandCategory.SYSTEM_ADMIN,
    "reg": CommandCategory.SYSTEM_ADMIN,
    "regedit": CommandCategory.SYSTEM_ADMIN,
    "sc": CommandCategory.SYSTEM_ADMIN,
    "schtasks": CommandCategory.SYSTEM_ADMIN,
    "wmic": CommandCategory.SYSTEM_ADMIN,
    "bcdedit": CommandCategory.SYSTEM_ADMIN,
    "diskpart": CommandCategory.SYSTEM_ADMIN,
    "format": CommandCategory.SYSTEM_ADMIN,
    "shutdown": CommandCategory.SYSTEM_ADMIN,
    "reboot": CommandCategory.SYSTEM_ADMIN,
    "restart": CommandCategory.SYSTEM_ADMIN,
    "halt": CommandCategory.SYSTEM_ADMIN,
    "poweroff": CommandCategory.SYSTEM_ADMIN,
    "taskkill": CommandCategory.SYSTEM_ADMIN,
    "kill": CommandCategory.SYSTEM_ADMIN,
    "pkill": CommandCategory.SYSTEM_ADMIN,
    "killall": CommandCategory.SYSTEM_ADMIN,
    # Privilege escalation
    "runas": CommandCategory.PRIVILEGE_ESCALATION,
    "sudo": CommandCategory.PRIVILEGE_ESCALATION,
    "su": CommandCategory.PRIVILEGE_ESCALATION,
    # Container
    "docker": CommandCategory.CONTAINER,
    "docker-compose": CommandCategory.CONTAINER,
    "podman": CommandCategory.CONTAINER,
    "kubectl": CommandCategory.CONTAINER,
    "helm": CommandCategory.CONTAINER,
    # Package managers
    "choco": CommandCategory.PACKAGE_MANAGER,
    "winget": CommandCategory.PACKAGE_MANAGER,
    "apt": CommandCategory.PACKAGE_MANAGER,
    "apt-get": CommandCategory.PACKAGE_MANAGER,
    "yum": CommandCategory.PACKAGE_MANAGER,
    "dnf": CommandCategory.PACKAGE_MANAGER,
    "pacman": CommandCategory.PACKAGE_MANAGER,
    "brew": CommandCategory.PACKAGE_MANAGER,
    "pip": CommandCategory.PACKAGE_MANAGER,
    "pip3": CommandCategory.PACKAGE_MANAGER,
    "npm": CommandCategory.PACKAGE_MANAGER,
    "yarn": CommandCategory.PACKAGE_MANAGER,
    "cargo": CommandCategory.PACKAGE_MANAGER,
    # Git
    "git": CommandCategory.GIT,
    # Filesystem
    "rm": CommandCategory.FILESYSTEM,
    "rmdir": CommandCategory.FILESYSTEM,
    "del": CommandCategory.FILESYSTEM,
    "rd": CommandCategory.FILESYSTEM,
    "cp": CommandCategory.FILESYSTEM,
    "mv": CommandCategory.FILESYSTEM,
    "mkdir": CommandCategory.FILESYSTEM,
    "ls": CommandCategory.FILESYSTEM,
    "dir": CommandCategory.FILESYSTEM,
    "cat": CommandCategory.FILESYSTEM,
    "type": CommandCategory.FILESYSTEM,
    "copy": CommandCategory.FILESYSTEM,
    "move": CommandCategory.FILESYSTEM,
    "xcopy": CommandCategory.FILESYSTEM,
    "robocopy": CommandCategory.FILESYSTEM,
    # Text processing
    "echo": CommandCategory.TEXT_PROCESSING,
    "grep": CommandCategory.TEXT_PROCESSING,
    "findstr": CommandCategory.TEXT_PROCESSING,
    "find": CommandCategory.TEXT_PROCESSING,
    "sort": CommandCategory.TEXT_PROCESSING,
    "more": CommandCategory.TEXT_PROCESSING,
    "head": CommandCategory.TEXT_PROCESSING,
    "awk": CommandCategory.TEXT_PROCESSING,
    "sed": CommandCategory.TEXT_PROCESSING,
}

# ---------------------------------------------------------------------------
# Additional argument-level checks
# ---------------------------------------------------------------------------

# Arguments that indicate privilege escalation regardless of the command
_ESCALATION_ARG_PATTERNS = frozenset(
    {
        "-RunAs",
        "/runas",
        "--privileged",  # docker --privileged
        "--user=root",
        "-u root",
        "runas",
    }
)


class CommandPolicyService:
    """Structural policy engine for terminal command authorization.

    This is the second line of defense.  Module 15 PermissionGate must
    have already allowed the request before this service is consulted.

    Security guarantees:
    - Never executes commands — classification only.
    - Never reads or interprets terminal output.
    - Policy tables are hard-coded; they cannot be overridden by user input.
    """

    def classify(self, request: CommandRequest) -> CommandClassification:
        """Classify a command request and return a policy verdict.

        Args:
            request: The command request to evaluate.

        Returns:
            CommandClassification with risk level, category, and allow/deny verdict.

        Raises:
            CommandPolicyRejectionError: If the command is explicitly blocked
                by structural policy (e.g., empty command, shell nesting).
        """
        cmd = request.command.strip()

        # 1. Reject empty commands
        if not cmd:
            raise CommandPolicyRejectionError("Command cannot be empty.")

        # 2. Reject commands containing path traversal or shell metacharacters
        #    when embedded in the command field itself
        blocked_chars = {"|", "&", ";", "`", "$", "(", ")", "<", ">", "\n", "\r"}
        if any(c in cmd for c in blocked_chars):
            raise CommandPolicyRejectionError(
                f"Command name '{cmd}' contains forbidden shell metacharacters."
            )

        # Normalize: extract bare executable name (strip path prefix if present)
        bare_cmd = cmd.replace("\\", "/").split("/")[-1].lower()
        # Also strip .exe suffix on Windows
        if bare_cmd.endswith(".exe"):
            bare_cmd = bare_cmd[:-4]

        # 3. Determine risk level
        risk_level = self._classify_risk(bare_cmd, request.args)

        # 4. Determine category
        category = _CATEGORY_MAP.get(bare_cmd, CommandCategory.UNKNOWN)

        # 5. Check for privilege escalation via arguments
        is_escalation = category == CommandCategory.PRIVILEGE_ESCALATION or self._args_indicate_escalation(request.args)
        if is_escalation:
            risk_level = CommandRiskLevel.CRITICAL

        # 6. Nested shell launch is always CRITICAL
        nested_shells = {"powershell", "cmd", "bash", "sh", "zsh", "fish", "ksh", "csh"}
        if bare_cmd in nested_shells:
            risk_level = CommandRiskLevel.CRITICAL

        # 7. Build notes
        notes: list[str] = []
        if risk_level == CommandRiskLevel.CRITICAL:
            notes.append(f"Command '{bare_cmd}' is classified CRITICAL. Elevated permission required.")
        elif risk_level == CommandRiskLevel.HIGH:
            notes.append(f"Command '{bare_cmd}' is classified HIGH risk.")
        if category == CommandCategory.NETWORK:
            notes.append("Network command — classified appropriately; not auto-blocked.")
        if category == CommandCategory.CONTAINER:
            notes.append("Container command — HIGH risk; careful review required.")

        is_allowed = risk_level != CommandRiskLevel.CRITICAL
        rejection_reason = (
            f"Command '{bare_cmd}' is classified CRITICAL and is blocked by structural policy. "
            "An explicit elevated permission grant from the user is required."
            if not is_allowed
            else None
        )

        return CommandClassification(
            command=cmd,
            args=request.args,
            category=category,
            risk_level=risk_level,
            is_allowed=is_allowed,
            rejection_reason=rejection_reason,
            requires_elevated_permission=risk_level == CommandRiskLevel.CRITICAL,
            notes=notes,
        )

    def _classify_risk(self, bare_cmd: str, args: list[str]) -> CommandRiskLevel:
        """Determine risk level from the bare command name."""
        if bare_cmd in _CRITICAL_COMMANDS:
            return CommandRiskLevel.CRITICAL
        if bare_cmd in _HIGH_RISK_COMMANDS:
            return CommandRiskLevel.HIGH
        if bare_cmd in _MEDIUM_RISK_COMMANDS:
            return CommandRiskLevel.MEDIUM
        return CommandRiskLevel.LOW

    @staticmethod
    def _args_indicate_escalation(args: list[str]) -> bool:
        """Detect privilege-escalation arguments regardless of command name."""
        lowered = {a.lower() for a in args}
        for pattern in _ESCALATION_ARG_PATTERNS:
            if pattern.lower() in lowered:
                return True
        return False
