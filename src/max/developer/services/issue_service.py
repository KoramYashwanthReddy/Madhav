"""Issue service for Module 23 — Developer Agent.

Manages DeveloperIssue objects in-memory.
GitHub API integration is a future layer beyond Module 23.
"""

import logging
from datetime import datetime, timezone

from max.developer.domain.enums import IssuePriority, IssueStatus
from max.developer.domain.exceptions import DevIssueNotFoundError, DevSessionNotFoundError
from max.developer.domain.models import DevAuditEvent, DeveloperIssue
from max.developer.repositories.repositories import (
    DevAuditRepository,
    DevIssueRepository,
    DevSessionRepository,
)

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IssueService:
    """Manages DeveloperIssue lifecycle for a developer session."""

    def __init__(
        self,
        session_repo: DevSessionRepository,
        issue_repo: DevIssueRepository,
        audit_repo: DevAuditRepository,
    ) -> None:
        self._session_repo = session_repo
        self._issue_repo = issue_repo
        self._audit_repo = audit_repo

    def create_issue(
        self,
        session_id: str,
        title: str,
        description: str = "",
        priority: IssuePriority = IssuePriority.MEDIUM,
        labels: list[str] | None = None,
        assignee: str | None = None,
    ) -> DeveloperIssue:
        """Create a new issue linked to a developer session."""
        session = self._session_repo.get(session_id)
        issue = DeveloperIssue(
            session_id=session_id,
            title=title,
            description=description,
            priority=priority,
            labels=labels or [],
            assignee=assignee,
        )
        self._issue_repo.save(issue)
        session.issue_ids.append(issue.id)
        self._session_repo.save(session)
        self._audit_repo.append(
            DevAuditEvent(
                session_id=session_id,
                event_type="ISSUE_CREATED",
                owner_id=session.owner_id,
                details={"issue_id": issue.id, "title": title},
            )
        )
        logger.info("Issue %s created in session %s: %s", issue.id, session_id, title)
        return issue

    def get_issue(self, issue_id: str) -> DeveloperIssue:
        """Retrieve an issue by ID."""
        return self._issue_repo.get(issue_id)

    def list_issues(self, session_id: str) -> list[DeveloperIssue]:
        """List all issues for a session."""
        return self._issue_repo.list_for_session(session_id)

    def update_issue_status(self, issue_id: str, status: IssueStatus) -> DeveloperIssue:
        """Update the status of an issue."""
        issue = self._issue_repo.get(issue_id)
        issue.status = status
        issue.updated_at = _utc_now()
        self._issue_repo.save(issue)
        self._audit_repo.append(
            DevAuditEvent(
                session_id=issue.session_id,
                event_type="ISSUE_STATUS_UPDATED",
                details={"issue_id": issue_id, "new_status": status.value},
            )
        )
        return issue

    def link_branch(self, issue_id: str, branch_name: str) -> DeveloperIssue:
        """Link a branch to an issue."""
        issue = self._issue_repo.get(issue_id)
        issue.linked_branch = branch_name
        issue.updated_at = _utc_now()
        self._issue_repo.save(issue)
        return issue

    def delete_issue(self, issue_id: str) -> bool:
        """Delete an issue."""
        return self._issue_repo.delete(issue_id)
