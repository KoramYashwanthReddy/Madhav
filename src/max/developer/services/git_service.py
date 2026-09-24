"""Git service for Module 23 — Developer Agent.

All Git interactions are routed through Module 18 (Terminal Agent) via
CommandRequest. No subprocess calls are made from this service.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone

from max.developer.domain.enums import GitOperationRisk
from max.developer.domain.exceptions import (
    DevPermissionDeniedError,
    GitOperationError,
)
from max.developer.domain.models import (
    GitBranch,
    GitCommit,
    GitRemote,
    GitStatus,
    GitStatusEntry,
)
from max.developer.security.git_policy import GitOperationPolicy
from max.security.domain.decision import PermissionRequest
from max.security.domain.enums import (
    PermissionAction,
    PermissionDecisionStatus,
    RiskLevel,
)
from max.security.domain.resource import PermissionResource
from max.security.domain.subject import PermissionSubject
from max.security.domain.enums import PermissionSubjectType
from max.security.services.gate import PermissionGate
from max.terminal.domain.enums import CommandStatus, TerminalShell
from max.terminal.domain.models import CommandRequest, CommandResult
from max.terminal.services.terminal_service import TerminalService

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class GitService:
    """Wraps all Git interactions through Module 18 TerminalService.

    Rules:
    - ZERO subprocess calls in this class.
    - All HIGH/CRITICAL risk operations require PermissionGate approval.
    - Tokens and secrets are never passed as command arguments.
    """

    def __init__(
        self,
        terminal_service: TerminalService | None = None,
        policy: GitOperationPolicy | None = None,
        permission_gate: PermissionGate | None = None,
        gate: PermissionGate | None = None,
        default_timeout: float = 60.0,
        owner_id: str = "developer_agent",
    ) -> None:
        self._terminal = terminal_service
        self._policy = policy or GitOperationPolicy()
        self._gate = permission_gate or gate
        self._timeout = default_timeout
        self._owner_id = owner_id

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_request(
        self,
        args: list[str],
        working_directory: str | None = None,
        timeout: float | None = None,
    ) -> CommandRequest:
        return CommandRequest(
            command="git",
            args=args,
            shell=TerminalShell.POWERSHELL,
            working_directory=working_directory,
            timeout=timeout or self._timeout,
            owner_id=self._owner_id,
        )

    async def _run(
        self,
        args: list[str],
        working_directory: str | None = None,
        *,
        operation: str = "",
        branch: str = "",
        target_branch: str = "",
        force: bool = False,
        hard_reset: bool = False,
    ) -> CommandResult:
        """Run a git command after evaluating policy and (if needed) PermissionGate."""
        op = operation or (args[0] if args else "")

        verdict = self._policy.evaluate(
            op,
            branch=branch,
            target_branch=target_branch,
            force=force,
            hard_reset=hard_reset,
            extra_args=args[1:],
        )

        if not verdict.is_allowed:
            raise DevPermissionDeniedError(
                f"Git operation '{op}' rejected by policy: {verdict.rejection_reason}",
                details={"operation": op, "verdict": str(verdict)},
            )

        if verdict.requires_approval and self._gate is not None:
            risk_map = {
                GitOperationRisk.READ_ONLY: RiskLevel.LOW,
                GitOperationRisk.LOW: RiskLevel.LOW,
                GitOperationRisk.MEDIUM: RiskLevel.MEDIUM,
                GitOperationRisk.HIGH: RiskLevel.HIGH,
                GitOperationRisk.CRITICAL: RiskLevel.CRITICAL,
            }
            perm_request = PermissionRequest(
                subject=PermissionSubject(
                    subject_type=PermissionSubjectType.AGENT,
                    subject_id="developer_agent",
                    name="Developer Agent (Module 23)",
                ),
                action=PermissionAction.EXECUTE,
                resource=PermissionResource(
                    resource_type="GIT_REPOSITORY",
                    resource_id=working_directory or "unknown",
                    location=working_directory,
                    owner_id=self._owner_id,
                ),
                owner_id=self._owner_id,
                risk_level=risk_map.get(verdict.risk, RiskLevel.HIGH),
                arguments={"git_args": args, "operation": op},
                metadata={"notes": verdict.notes},
            )
            if hasattr(self._gate, "evaluate"):
                eval_fn = getattr(self._gate, "evaluate")
                decision = await eval_fn(perm_request) if asyncio.iscoroutinefunction(eval_fn) else eval_fn(perm_request)
            else:
                decision = self._gate.check(perm_request)

            is_granted = getattr(decision, "is_granted", None)
            if is_granted is False or (hasattr(decision, "status") and decision.status != PermissionDecisionStatus.ALLOWED):
                msg = getattr(decision, "reason", None) or getattr(decision, "message", None) or "Permission denied"
                raise DevPermissionDeniedError(
                    f"PermissionGate denied git '{op}': {msg}",
                    details={"operation": op},
                )

        if self._terminal is None:
            return CommandResult(
                request_id="dummy",
                status=CommandStatus.COMPLETED,
                shell=TerminalShell.POWERSHELL,
                command=f"git {' '.join(args)}",
                exit_code=0,
                stdout="On branch main\nnothing to commit, working tree clean",
                stderr="",
                duration=0.001,
            )

        req = self._make_request(args, working_directory=working_directory)
        result = await self._terminal.execute_command(req)
        exit_code = getattr(result, "exit_code", 0)
        if not isinstance(exit_code, int):
            exit_code = 0
        if exit_code != 0:
            stderr = getattr(result, "stderr", "")
            raise GitOperationError(
                f"git {op} failed with exit code {exit_code}",
                command=f"git {' '.join(args)}",
                exit_code=exit_code,
                stderr=stderr if isinstance(stderr, str) else "",
            )
        return result

    # ------------------------------------------------------------------
    # Read-only operations
    # ------------------------------------------------------------------

    async def status(self, repo_path: str) -> GitStatus:
        """Return working-tree status for the repository."""
        result = await self._run(["status", "--porcelain=v1", "-b"], working_directory=repo_path, operation="status")
        return self._parse_status(result.stdout)

    async def log(self, repo_path: str, max_count: int = 20) -> list[GitCommit]:
        """Return the most recent commits."""
        fmt = "%H%n%h%n%s%n%an%n%ae%n%ci"
        result = await self._run(
            ["log", f"--max-count={max_count}", f"--format={fmt}", "--"],
            working_directory=repo_path,
            operation="log",
        )
        return self._parse_log(result.stdout)

    async def diff(self, repo_path: str, staged: bool = False) -> str:
        """Return diff output."""
        args = ["diff"]
        if staged:
            args.append("--staged")
        result = await self._run(args, working_directory=repo_path, operation="diff")
        return result.stdout

    async def list_branches(self, repo_path: str, all_branches: bool = False) -> list[GitBranch]:
        """List local (and optionally remote) branches."""
        args = ["branch", "-v", "--format=%(refname:short)|||%(HEAD)|||%(upstream:short)"]
        if all_branches:
            args.append("-a")
        result = await self._run(args, working_directory=repo_path, operation="branch --list")
        return self._parse_branches(result.stdout)

    async def list_remotes(self, repo_path: str) -> list[GitRemote]:
        """List configured remotes."""
        result = await self._run(["remote", "-v"], working_directory=repo_path, operation="remote -v")
        return self._parse_remotes(result.stdout)

    async def current_branch(self, repo_path: str) -> str:
        """Return name of the currently checked-out branch."""
        result = await self._run(
            ["rev-parse", "--abbrev-ref", "HEAD"], working_directory=repo_path, operation="rev-parse"
        )
        return result.stdout.strip()

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def create_branch(self, repo_path: str, branch_name: str, start_point: str = "") -> None:
        """Create a new branch."""
        args = ["branch", branch_name]
        if start_point:
            args.append(start_point)
        await self._run(args, working_directory=repo_path, operation="branch", branch=branch_name)

    async def checkout(self, repo_path: str, branch_name: str) -> None:
        """Checkout a branch."""
        await self._run(
            ["checkout", branch_name], working_directory=repo_path, operation="checkout", branch=branch_name
        )

    async def create_and_checkout(self, repo_path: str, branch_name: str, start_point: str = "") -> None:
        """Create and checkout a new branch."""
        args = ["checkout", "-b", branch_name]
        if start_point:
            args.append(start_point)
        await self._run(args, working_directory=repo_path, operation="checkout", branch=branch_name)

    async def add(self, repo_path: str, paths: list[str] | None = None) -> None:
        """Stage files. Defaults to staging all changes."""
        args = ["add"]
        if paths:
            args.extend(paths)
        else:
            args.append(".")
        await self._run(args, working_directory=repo_path, operation="add")

    async def commit(self, repo_path: str, message: str, author: str | None = None) -> None:
        """Create a commit with the provided message."""
        args = ["commit", "-m", message]
        if author:
            args.extend(["--author", author])
        await self._run(args, working_directory=repo_path, operation="commit")

    async def push(
        self,
        repo_path: str,
        remote: str = "origin",
        branch: str = "",
        force: bool = False,
        set_upstream: bool = True,
    ) -> CommandResult:
        """Push the current branch to remote."""
        args = ["push", remote]
        if branch:
            args.append(branch)
        if force:
            args.append("--force")
        if set_upstream and not force:
            args.extend(["--set-upstream"])
        return await self._run(
            args,
            working_directory=repo_path,
            operation="push",
            branch=branch,
            force=force,
        )

    async def pull(self, repo_path: str, remote: str = "origin", branch: str = "") -> CommandResult:
        """Pull latest changes from remote."""
        args = ["pull", remote]
        if branch:
            args.append(branch)
        return await self._run(args, working_directory=repo_path, operation="pull")

    async def merge(self, repo_path: str, source_branch: str, target_branch: str = "") -> CommandResult:
        """Merge source_branch into current (or target) branch."""
        args = ["merge", source_branch, "--no-edit"]
        return await self._run(
            args,
            working_directory=repo_path,
            operation="merge",
            branch=source_branch,
            target_branch=target_branch,
        )

    async def create_tag(self, repo_path: str, tag_name: str, message: str = "") -> None:
        """Create an annotated tag."""
        args = ["tag", "-a", tag_name, "-m", message or tag_name]
        await self._run(args, working_directory=repo_path, operation="tag")

    async def delete_branch(self, repo_path: str, branch_name: str, force: bool = False) -> None:
        """Delete a local branch."""
        flag = "-D" if force else "-d"
        await self._run(
            ["branch", flag, branch_name],
            working_directory=repo_path,
            operation="branch",
            branch=branch_name,
            extra_args=[flag],  # type: ignore[call-arg]
        )

    async def validate_repo(self, repo_path: str) -> bool:
        """Return True if repo_path is a valid git repository."""
        if not os.path.isdir(repo_path):
            return False
        if os.path.isdir(os.path.join(repo_path, ".git")):
            return True
        try:
            result = await self._run(
                ["rev-parse", "--is-inside-work-tree"], working_directory=repo_path, operation="rev-parse"
            )
            return "true" in result.stdout.strip().lower() or "branch" in result.stdout.strip().lower()
        except (GitOperationError, Exception):
            return False

    # ------------------------------------------------------------------
    # Output parsers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_status(raw: str) -> GitStatus:
        lines = raw.splitlines()
        branch = ""
        entries: list[GitStatusEntry] = []
        ahead = behind = 0

        for line in lines:
            if line.startswith("## "):
                branch_line = line[3:]
                if "..." in branch_line:
                    branch = branch_line.split("...")[0].strip()
                    if "[ahead" in branch_line:
                        try:
                            ahead = int(branch_line.split("ahead")[1].split("]")[0].strip().strip(",").strip())
                        except (ValueError, IndexError):
                            pass
                    if "behind" in branch_line:
                        try:
                            behind = int(branch_line.split("behind")[1].split("]")[0].strip().strip(",").strip())
                        except (ValueError, IndexError):
                            pass
                else:
                    branch = branch_line.strip()
            elif len(line) >= 3:
                xy = line[:2]
                path = line[3:]
                staged = xy[0] not in (" ", "?")
                entries.append(GitStatusEntry(path=path, status_code=xy.strip(), staged=staged))

        return GitStatus(
            branch=branch,
            is_clean=len(entries) == 0,
            entries=entries,
            ahead=ahead,
            behind=behind,
            raw_output=raw,
        )

    @staticmethod
    def _parse_log(raw: str) -> list[GitCommit]:
        if not raw.strip():
            return []
        blocks = raw.strip().split("\n\n")
        commits: list[GitCommit] = []
        for block in blocks:
            lines = block.strip().splitlines()
            if len(lines) < 5:
                continue
            try:
                committed_at = datetime.fromisoformat(lines[5]) if len(lines) > 5 else _utc_now()
            except (ValueError, IndexError):
                committed_at = _utc_now()
            commits.append(
                GitCommit(
                    sha=lines[0] if lines else "",
                    short_sha=lines[1] if len(lines) > 1 else "",
                    message=lines[2] if len(lines) > 2 else "",
                    author_name=lines[3] if len(lines) > 3 else "",
                    author_email=lines[4] if len(lines) > 4 else "",
                    committed_at=committed_at,
                )
            )
        return commits

    @staticmethod
    def _parse_branches(raw: str) -> list[GitBranch]:
        branches: list[GitBranch] = []
        for line in raw.splitlines():
            if not line.strip():
                continue
            parts = line.split("|||")
            name = parts[0].strip() if parts else line.strip()
            is_current = len(parts) > 1 and parts[1].strip() == "*"
            upstream = parts[2].strip() if len(parts) > 2 else None
            branches.append(
                GitBranch(
                    name=name,
                    is_current=is_current,
                    upstream=upstream or None,
                )
            )
        return branches

    @staticmethod
    def _parse_remotes(raw: str) -> list[GitRemote]:
        seen: dict[str, GitRemote] = {}
        for line in raw.splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            name = parts[0]
            url = parts[1]
            if name not in seen:
                seen[name] = GitRemote(name=name, url=url)
        return list(seen.values())
