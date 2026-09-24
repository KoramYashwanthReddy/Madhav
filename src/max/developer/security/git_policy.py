"""Git operation risk policy for Module 23 — Developer Agent.

All dangerous Git operations (force-push, reset --hard, merging to protected
branches, deleting protected branches) are classified here. Module 23 consults
this policy before submitting CommandRequest to Module 18, and requests
PermissionGate approval for HIGH/CRITICAL risk operations.
"""

from dataclasses import dataclass, field

from max.developer.domain.enums import GitOperationRisk


@dataclass
class PolicyVerdict:
    """Result of a Git operation policy evaluation."""

    operation: str
    risk: GitOperationRisk
    is_allowed: bool
    requires_approval: bool = False
    rejection_reason: str | None = None
    notes: list[str] = field(default_factory=list)


class GitOperationPolicy:
    """Classifies Git operations by risk and enforces policy rules.

    This class does NOT call PermissionGate directly — it only produces
    a ``PolicyVerdict``. The caller (GitService) is responsible for
    requesting approval via PermissionGate when ``requires_approval=True``.
    """

    # Read-only operations — always allowed, no approval needed
    _READ_ONLY_OPERATIONS: frozenset[str] = frozenset(
        {
            "status",
            "log",
            "diff",
            "show",
            "branch --list",
            "branch -a",
            "remote -v",
            "rev-parse",
            "rev-list",
            "ls-files",
            "describe",
        }
    )

    # Operations that are always blocked (never permitted via this policy)
    _BLOCKED_OPERATIONS: frozenset[str] = frozenset(
        {
            "bisect",   # interactive session — not supported
        }
    )

    def __init__(self, protected_branches: list[str] | None = None) -> None:
        self._protected_branches: list[str] = protected_branches or ["main", "master", "release"]

    def _is_protected(self, branch: str) -> bool:
        return branch in self._protected_branches

    def evaluate(
        self,
        operation: str,
        *,
        branch: str = "",
        target_branch: str = "",
        force: bool = False,
        hard_reset: bool = False,
        extra_args: list[str] | None = None,
    ) -> PolicyVerdict:
        """Evaluate the risk and policy verdict for a Git operation.

        Parameters
        ----------
        operation:
            The Git subcommand (e.g. ``"push"``, ``"merge"``, ``"commit"``).
        branch:
            The source branch involved in the operation.
        target_branch:
            The destination branch (for merges, push, etc.).
        force:
            Whether ``--force`` or ``-f`` is requested.
        hard_reset:
            Whether ``--hard`` is specified on a ``reset`` operation.
        extra_args:
            Additional CLI args for context (not executed here).
        """
        extra_args = extra_args or []
        op = operation.strip().lower()

        # ── Blocked operations ─────────────────────────────────────────────
        if op in self._BLOCKED_OPERATIONS:
            return PolicyVerdict(
                operation=op,
                risk=GitOperationRisk.CRITICAL,
                is_allowed=False,
                rejection_reason=f"Operation '{op}' is unconditionally blocked by policy.",
            )

        # ── Read-only operations ────────────────────────────────────────────
        if op in self._READ_ONLY_OPERATIONS:
            return PolicyVerdict(
                operation=op,
                risk=GitOperationRisk.READ_ONLY,
                is_allowed=True,
            )

        # ── Force push ──────────────────────────────────────────────────────
        if op == "push" and (force or "--force" in extra_args or "-f" in extra_args):
            return PolicyVerdict(
                operation=op,
                risk=GitOperationRisk.HIGH,
                is_allowed=True,
                requires_approval=True,
                notes=["Force push rewrites remote history. Explicit approval required."],
            )

        # ── Push to protected branch ────────────────────────────────────────
        if op == "push" and self._is_protected(target_branch or branch):
            return PolicyVerdict(
                operation=op,
                risk=GitOperationRisk.MEDIUM,
                is_allowed=True,
                requires_approval=False,
                notes=[f"Push targets protected branch '{target_branch or branch}'."],
            )

        # ── Regular push ────────────────────────────────────────────────────
        if op == "push":
            return PolicyVerdict(
                operation=op,
                risk=GitOperationRisk.LOW,
                is_allowed=True,
            )

        # ── Merge into protected branch ─────────────────────────────────────
        if op == "merge" and self._is_protected(target_branch or branch):
            return PolicyVerdict(
                operation=op,
                risk=GitOperationRisk.HIGH,
                is_allowed=True,
                requires_approval=True,
                notes=[f"Merging into protected branch '{target_branch or branch}' requires approval."],
            )

        # ── Rebase on protected branch ──────────────────────────────────────
        if op == "rebase" and self._is_protected(target_branch or branch):
            return PolicyVerdict(
                operation=op,
                risk=GitOperationRisk.HIGH,
                is_allowed=True,
                requires_approval=True,
                notes=[f"Rebasing onto protected branch '{target_branch or branch}' requires approval."],
            )

        # ── Hard reset ──────────────────────────────────────────────────────
        if op == "reset" and (hard_reset or "--hard" in extra_args):
            return PolicyVerdict(
                operation=op,
                risk=GitOperationRisk.HIGH,
                is_allowed=True,
                requires_approval=True,
                notes=["Hard reset discards uncommitted work. Explicit approval required."],
            )

        # ── Delete protected branch ─────────────────────────────────────────
        if op in {"branch"} and ("-d" in extra_args or "-D" in extra_args or "--delete" in extra_args):
            if self._is_protected(branch):
                return PolicyVerdict(
                    operation=op,
                    risk=GitOperationRisk.CRITICAL,
                    is_allowed=True,
                    requires_approval=True,
                    notes=[f"Deleting protected branch '{branch}' is a critical operation."],
                )
            return PolicyVerdict(
                operation=op,
                risk=GitOperationRisk.MEDIUM,
                is_allowed=True,
                requires_approval=False,
            )

        # ── Commit ──────────────────────────────────────────────────────────
        if op == "commit":
            return PolicyVerdict(
                operation=op,
                risk=GitOperationRisk.LOW,
                is_allowed=True,
            )

        # ── Checkout / switch ───────────────────────────────────────────────
        if op in {"checkout", "switch"}:
            return PolicyVerdict(
                operation=op,
                risk=GitOperationRisk.LOW,
                is_allowed=True,
            )

        # ── Pull / fetch ────────────────────────────────────────────────────
        if op in {"pull", "fetch"}:
            return PolicyVerdict(
                operation=op,
                risk=GitOperationRisk.LOW,
                is_allowed=True,
            )

        # ── Tag ─────────────────────────────────────────────────────────────
        if op == "tag":
            return PolicyVerdict(
                operation=op,
                risk=GitOperationRisk.LOW,
                is_allowed=True,
            )

        # ── Default: medium risk, allowed without approval ──────────────────
        return PolicyVerdict(
            operation=op,
            risk=GitOperationRisk.MEDIUM,
            is_allowed=True,
            notes=[f"Unclassified operation '{op}' defaulting to MEDIUM risk."],
        )
