"""In-memory repositories for Module 23 — Developer Agent."""

from datetime import datetime, timezone

from max.developer.domain.exceptions import (
    DevIssueNotFoundError,
    DevPRNotFoundError,
    DevSessionNotFoundError,
    DevWorkflowNotFoundError,
)
from max.developer.domain.models import (
    DevAuditEvent,
    DeveloperIssue,
    DeveloperSession,
    DeveloperWorkflow,
    PullRequest,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DevSessionRepository:
    """In-memory CRUD store for DeveloperSession objects."""

    def __init__(self) -> None:
        self._store: dict[str, DeveloperSession] = {}

    def save(self, session: DeveloperSession) -> DeveloperSession:
        session.updated_at = _utc_now()
        self._store[session.id] = session
        return session

    def get(self, session_id: str) -> DeveloperSession:
        try:
            return self._store[session_id]
        except KeyError:
            raise DevSessionNotFoundError(
                f"Developer session '{session_id}' not found.",
                details={"session_id": session_id},
            )

    def list_all(self, owner_id: str | None = None) -> list[DeveloperSession]:
        sessions = list(self._store.values())
        if owner_id is not None:
            sessions = [s for s in sessions if s.owner_id == owner_id]
        return sessions

    def delete(self, session_id: str) -> bool:
        return self._store.pop(session_id, None) is not None

    def exists(self, session_id: str) -> bool:
        return session_id in self._store


class DevWorkflowRepository:
    """In-memory CRUD store for DeveloperWorkflow objects."""

    def __init__(self) -> None:
        self._store: dict[str, DeveloperWorkflow] = {}

    def save(self, workflow: DeveloperWorkflow) -> DeveloperWorkflow:
        workflow.updated_at = _utc_now()
        self._store[workflow.id] = workflow
        return workflow

    def get(self, workflow_id: str) -> DeveloperWorkflow:
        try:
            return self._store[workflow_id]
        except KeyError:
            raise DevWorkflowNotFoundError(
                f"Developer workflow '{workflow_id}' not found.",
                details={"workflow_id": workflow_id},
            )

    def list_for_session(self, session_id: str) -> list[DeveloperWorkflow]:
        return [w for w in self._store.values() if w.session_id == session_id]

    def delete(self, workflow_id: str) -> bool:
        return self._store.pop(workflow_id, None) is not None


class DevIssueRepository:
    """In-memory CRUD store for DeveloperIssue objects."""

    def __init__(self) -> None:
        self._store: dict[str, DeveloperIssue] = {}

    def save(self, issue: DeveloperIssue) -> DeveloperIssue:
        issue.updated_at = _utc_now()
        self._store[issue.id] = issue
        return issue

    def get(self, issue_id: str) -> DeveloperIssue:
        try:
            return self._store[issue_id]
        except KeyError:
            raise DevIssueNotFoundError(
                f"Developer issue '{issue_id}' not found.",
                details={"issue_id": issue_id},
            )

    def list_for_session(self, session_id: str) -> list[DeveloperIssue]:
        return [i for i in self._store.values() if i.session_id == session_id]

    def delete(self, issue_id: str) -> bool:
        return self._store.pop(issue_id, None) is not None


class DevPRRepository:
    """In-memory CRUD store for PullRequest objects."""

    def __init__(self) -> None:
        self._store: dict[str, PullRequest] = {}

    def save(self, pr: PullRequest) -> PullRequest:
        pr.updated_at = _utc_now()
        self._store[pr.id] = pr
        return pr

    def get(self, pr_id: str) -> PullRequest:
        try:
            return self._store[pr_id]
        except KeyError:
            raise DevPRNotFoundError(
                f"Pull request '{pr_id}' not found.",
                details={"pr_id": pr_id},
            )

    def list_for_session(self, session_id: str) -> list[PullRequest]:
        return [p for p in self._store.values() if p.session_id == session_id]

    def delete(self, pr_id: str) -> bool:
        return self._store.pop(pr_id, None) is not None


class DevAuditRepository:
    """Append-only audit log for Developer Agent events."""

    def __init__(self) -> None:
        self._events: list[DevAuditEvent] = []

    def append(self, event: DevAuditEvent) -> None:
        self._events.append(event)

    def list_for_session(self, session_id: str) -> list[DevAuditEvent]:
        return [e for e in self._events if e.session_id == session_id]

    def list_all(self) -> list[DevAuditEvent]:
        return list(self._events)
