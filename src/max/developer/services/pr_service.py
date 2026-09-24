"""PR service for Module 23 — Developer Agent.

Manages PullRequest lifecycle. Merge operations into protected branches
require PermissionGate approval before proceeding.
"""

import logging
from datetime import UTC, datetime

from max.developer.domain.enums import MergeStrategy, PRStatus
from max.developer.domain.exceptions import (
    PRConflictError,
)
from max.developer.domain.models import DevAuditEvent, PullRequest
from max.developer.repositories.repositories import (
    DevAuditRepository,
    DevPRRepository,
    DevSessionRepository,
)
from max.developer.services.git_service import GitService

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class PRService:
    """Manages PullRequest lifecycle for a developer session.

    Merge operations into protected branches trigger PermissionGate approval
    via GitService (which already applies the policy verdict).
    """

    def __init__(
        self,
        session_repo: DevSessionRepository,
        pr_repo: DevPRRepository,
        audit_repo: DevAuditRepository,
        git_service: GitService,
        protected_branches: list[str] | None = None,
        require_approval_for_merge: bool = True,
    ) -> None:
        self._session_repo = session_repo
        self._pr_repo = pr_repo
        self._audit_repo = audit_repo
        self._git = git_service
        self._protected_branches = protected_branches or ["main", "master", "release"]
        self._require_approval_for_merge = require_approval_for_merge

    def create_pr(
        self,
        session_id: str,
        title: str,
        source_branch: str,
        target_branch: str,
        description: str = "",
        reviewers: list[str] | None = None,
        merge_strategy: MergeStrategy = MergeStrategy.MERGE_COMMIT,
        linked_issue_id: str | None = None,
        linked_workflow_id: str | None = None,
    ) -> PullRequest:
        """Create a new pull request record."""
        session = self._session_repo.get(session_id)
        pr = PullRequest(
            session_id=session_id,
            title=title,
            description=description,
            source_branch=source_branch,
            target_branch=target_branch,
            status=PRStatus.DRAFT,
            merge_strategy=merge_strategy,
            reviewers=reviewers or [],
            linked_issue_id=linked_issue_id,
            linked_workflow_id=linked_workflow_id,
        )
        self._pr_repo.save(pr)
        session.pr_ids.append(pr.id)
        self._session_repo.save(session)
        self._audit_repo.append(
            DevAuditEvent(
                session_id=session_id,
                event_type="PR_CREATED",
                owner_id=session.owner_id,
                details={
                    "pr_id": pr.id,
                    "source_branch": source_branch,
                    "target_branch": target_branch,
                },
            )
        )
        logger.info("PR %s created: %s → %s", pr.id, source_branch, target_branch)
        return pr

    def get_pr(self, pr_id: str) -> PullRequest:
        """Retrieve a PR by ID."""
        return self._pr_repo.get(pr_id)

    def list_prs(self, session_id: str) -> list[PullRequest]:
        """List all PRs for a session."""
        return self._pr_repo.list_for_session(session_id)

    def open_pr(self, pr_id: str) -> PullRequest:
        """Move PR from DRAFT to OPEN status."""
        pr = self._pr_repo.get(pr_id)
        pr.status = PRStatus.OPEN
        pr.updated_at = _utc_now()
        self._pr_repo.save(pr)
        return pr

    def request_review(self, pr_id: str, reviewers: list[str]) -> PullRequest:
        """Add reviewers and advance PR to REVIEW_REQUESTED."""
        pr = self._pr_repo.get(pr_id)
        pr.reviewers = list(set(pr.reviewers + reviewers))
        pr.status = PRStatus.REVIEW_REQUESTED
        pr.updated_at = _utc_now()
        self._pr_repo.save(pr)
        return pr

    def approve_pr(self, pr_id: str) -> PullRequest:
        """Mark PR as APPROVED."""
        pr = self._pr_repo.get(pr_id)
        pr.status = PRStatus.APPROVED
        pr.updated_at = _utc_now()
        self._pr_repo.save(pr)
        return pr

    async def merge_pr(self, pr_id: str, repo_path: str) -> PullRequest:
        """Merge the PR's source branch into its target branch.

        Uses GitService.merge(), which evaluates the policy and requests
        PermissionGate approval for protected-branch merges.
        """
        pr = self._pr_repo.get(pr_id)
        if pr.status not in {PRStatus.OPEN, PRStatus.APPROVED, PRStatus.REVIEW_REQUESTED}:
            raise PRConflictError(
                f"Cannot merge PR '{pr_id}' in status '{pr.status.value}'.",
                details={"pr_id": pr_id, "status": pr.status.value},
            )

        try:
            # Checkout target branch, then merge source
            await self._git.checkout(repo_path, pr.target_branch)
            await self._git.merge(
                repo_path,
                source_branch=pr.source_branch,
                target_branch=pr.target_branch,
            )
        except Exception as exc:
            raise PRConflictError(
                f"Merge of PR '{pr_id}' failed: {exc}",
                details={"pr_id": pr_id, "error": str(exc)},
            ) from exc

        pr.status = PRStatus.MERGED
        pr.merged_at = _utc_now()
        pr.updated_at = _utc_now()
        self._pr_repo.save(pr)

        session = self._session_repo.get(pr.session_id)
        self._audit_repo.append(
            DevAuditEvent(
                session_id=pr.session_id,
                event_type="PR_MERGED",
                owner_id=session.owner_id,
                details={
                    "pr_id": pr_id,
                    "source_branch": pr.source_branch,
                    "target_branch": pr.target_branch,
                },
            )
        )
        logger.info("PR %s merged: %s → %s", pr_id, pr.source_branch, pr.target_branch)
        return pr

    def close_pr(self, pr_id: str) -> PullRequest:
        """Close a PR without merging."""
        pr = self._pr_repo.get(pr_id)
        pr.status = PRStatus.CLOSED
        pr.updated_at = _utc_now()
        self._pr_repo.save(pr)
        return pr
