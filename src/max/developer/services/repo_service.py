"""Repository service for Module 23 — Developer Agent.

Manages DeveloperSession lifecycle and repository introspection.
"""

import logging
import os

from max.developer.domain.enums import DevSessionStatus
from max.developer.domain.exceptions import DevSessionNotFoundError, RepositoryNotFoundError
from max.developer.domain.models import DeveloperSession, Repository
from max.developer.repositories.repositories import DevAuditRepository, DevSessionRepository
from max.developer.services.git_service import GitService
from max.developer.domain.models import DevAuditEvent

logger = logging.getLogger(__name__)


class RepoService:
    """Manages DeveloperSession lifecycle and repository metadata."""

    def __init__(
        self,
        session_repo: DevSessionRepository,
        audit_repo: DevAuditRepository,
        git_service: GitService,
        default_branch: str = "main",
        max_sessions: int = 20,
    ) -> None:
        self._session_repo = session_repo
        self._audit_repo = audit_repo
        self._git = git_service
        self._default_branch = default_branch
        self._max_sessions = max_sessions

    async def open_session(self, repo_path: str, owner_id: str = "user_default") -> DeveloperSession:
        """Open a new DeveloperSession for the specified repository path."""
        # Validate that path exists
        if not os.path.isdir(repo_path):
            raise RepositoryNotFoundError(
                f"Repository path does not exist: {repo_path}",
                details={"repo_path": repo_path},
            )

        # Validate git repository
        is_valid = await self._git.validate_repo(repo_path)
        if not is_valid:
            raise RepositoryNotFoundError(
                f"Path is not a valid Git repository: {repo_path}",
                details={"repo_path": repo_path},
            )

        # Introspect repository
        repo_name = os.path.basename(os.path.abspath(repo_path))
        current_branch = ""
        remotes = []
        try:
            current_branch = await self._git.current_branch(repo_path)
            remotes = await self._git.list_remotes(repo_path)
        except Exception:
            pass

        repo = Repository(
            path=repo_path,
            name=repo_name,
            default_branch=self._default_branch,
            current_branch=current_branch,
            remotes=remotes,
            is_valid_git_repo=True,
        )

        session = DeveloperSession(
            repo_path=repo_path,
            owner_id=owner_id,
            status=DevSessionStatus.OPEN,
            repository=repo,
        )
        self._session_repo.save(session)

        self._audit_repo.append(
            DevAuditEvent(
                session_id=session.id,
                event_type="SESSION_OPENED",
                owner_id=owner_id,
                details={"repo_path": repo_path, "current_branch": current_branch},
            )
        )
        logger.info("Developer session %s opened for repo: %s", session.id, repo_path)
        return session

    def get_session(self, session_id: str) -> DeveloperSession:
        """Retrieve a session by ID."""
        return self._session_repo.get(session_id)

    def list_sessions(self, owner_id: str | None = None) -> list[DeveloperSession]:
        """List all sessions, optionally filtered by owner."""
        return self._session_repo.list_all(owner_id=owner_id)

    def close_session(self, session_id: str) -> DeveloperSession:
        """Close a developer session."""
        from datetime import datetime, timezone
        session = self._session_repo.get(session_id)
        session.status = DevSessionStatus.CLOSED
        session.closed_at = datetime.now(timezone.utc)
        self._session_repo.save(session)
        self._audit_repo.append(
            DevAuditEvent(
                session_id=session_id,
                event_type="SESSION_CLOSED",
                owner_id=session.owner_id,
            )
        )
        logger.info("Developer session %s closed.", session_id)
        return session

    def delete_session(self, session_id: str) -> bool:
        """Delete a session record."""
        return self._session_repo.delete(session_id)
