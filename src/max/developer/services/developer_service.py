"""Developer service facade for Module 23 — Developer Agent.

Provides a unified API that combines RepoService, IssueService,
PRService, WorkflowService, and GitService.
"""

import logging

from max.developer.domain.enums import IssuePriority, IssueStatus, MergeStrategy, WorkflowType
from max.developer.domain.models import (
    DeveloperIssue,
    DeveloperSession,
    DeveloperWorkflow,
    GitStatus,
    PullRequest,
)
from max.developer.services.git_service import GitService
from max.developer.services.issue_service import IssueService
from max.developer.services.pr_service import PRService
from max.developer.services.repo_service import RepoService
from max.developer.services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)


class DeveloperService:
    """Unified Developer Agent service facade.

    All public methods in this class delegate to specialized sub-services.
    The facade exists to simplify dependency wiring in the container
    and to give the API routes a single injection point.
    """

    def __init__(
        self,
        repo_service: RepoService,
        issue_service: IssueService,
        pr_service: PRService,
        workflow_service: WorkflowService,
        git_service: GitService,
    ) -> None:
        self._repo = repo_service
        self._issues = issue_service
        self._prs = pr_service
        self._workflows = workflow_service
        self._git = git_service

    # ------------------------------------------------------------------
    # Session
    # ------------------------------------------------------------------

    async def open_session(self, repo_path: str, owner_id: str = "user_default") -> DeveloperSession:
        return await self._repo.open_session(repo_path, owner_id=owner_id)

    def get_session(self, session_id: str) -> DeveloperSession:
        return self._repo.get_session(session_id)

    def list_sessions(self, owner_id: str | None = None) -> list[DeveloperSession]:
        return self._repo.list_sessions(owner_id=owner_id)

    def close_session(self, session_id: str) -> DeveloperSession:
        return self._repo.close_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        return self._repo.delete_session(session_id)

    # ------------------------------------------------------------------
    # Git operations
    # ------------------------------------------------------------------

    async def get_git_status(self, session_id: str) -> GitStatus:
        session = self._repo.get_session(session_id)
        return await self._git.status(session.repo_path)

    async def create_branch(
        self, session_id: str, branch_name: str, start_point: str = ""
    ) -> dict[str, str]:
        session = self._repo.get_session(session_id)
        await self._git.create_and_checkout(session.repo_path, branch_name, start_point)
        return {"session_id": session_id, "branch": branch_name, "status": "CREATED"}

    async def checkout_branch(self, session_id: str, branch_name: str) -> dict[str, str]:
        session = self._repo.get_session(session_id)
        await self._git.checkout(session.repo_path, branch_name)
        return {"session_id": session_id, "branch": branch_name, "status": "CHECKED_OUT"}

    async def get_log(self, session_id: str, max_count: int = 20) -> list[dict]:
        session = self._repo.get_session(session_id)
        commits = await self._git.log(session.repo_path, max_count=max_count)
        return [c.model_dump() for c in commits]

    async def stage_and_commit(
        self, session_id: str, message: str, paths: list[str] | None = None
    ) -> dict[str, str]:
        session = self._repo.get_session(session_id)
        await self._git.add(session.repo_path, paths=paths)
        await self._git.commit(session.repo_path, message)
        return {"session_id": session_id, "status": "COMMITTED", "message": message}

    async def push(
        self,
        session_id: str,
        remote: str = "origin",
        branch: str = "",
        force: bool = False,
    ) -> dict[str, str]:
        session = self._repo.get_session(session_id)
        await self._git.push(session.repo_path, remote=remote, branch=branch, force=force)
        return {"session_id": session_id, "status": "PUSHED", "remote": remote}

    async def pull(self, session_id: str, remote: str = "origin", branch: str = "") -> dict[str, str]:
        session = self._repo.get_session(session_id)
        await self._git.pull(session.repo_path, remote=remote, branch=branch)
        return {"session_id": session_id, "status": "PULLED", "remote": remote}

    # ------------------------------------------------------------------
    # Workflows
    # ------------------------------------------------------------------

    def start_workflow(
        self,
        session_id: str,
        workflow_type: WorkflowType,
        objective: str,
        branch_name: str | None = None,
        linked_issue_id: str | None = None,
    ) -> DeveloperWorkflow:
        return self._workflows.start_workflow(
            session_id=session_id,
            workflow_type=workflow_type,
            objective=objective,
            branch_name=branch_name,
            linked_issue_id=linked_issue_id,
        )

    def get_workflow(self, workflow_id: str) -> DeveloperWorkflow:
        return self._workflows.get_workflow(workflow_id)

    def list_workflows(self, session_id: str) -> list[DeveloperWorkflow]:
        return self._workflows.list_workflows(session_id)

    async def advance_workflow(
        self,
        workflow_id: str,
        commit_message: str = "",
        coding_session_id: str | None = None,
        tag_name: str | None = None,
    ) -> DeveloperWorkflow:
        return await self._workflows.advance_workflow(
            workflow_id=workflow_id,
            commit_message=commit_message,
            coding_session_id=coding_session_id,
            tag_name=tag_name,
        )

    def cancel_workflow(self, workflow_id: str) -> DeveloperWorkflow:
        return self._workflows.cancel_workflow(workflow_id)

    # ------------------------------------------------------------------
    # Issues
    # ------------------------------------------------------------------

    def create_issue(
        self,
        session_id: str,
        title: str,
        description: str = "",
        priority: IssuePriority = IssuePriority.MEDIUM,
        labels: list[str] | None = None,
        assignee: str | None = None,
    ) -> DeveloperIssue:
        return self._issues.create_issue(
            session_id=session_id,
            title=title,
            description=description,
            priority=priority,
            labels=labels,
            assignee=assignee,
        )

    def get_issue(self, issue_id: str) -> DeveloperIssue:
        return self._issues.get_issue(issue_id)

    def list_issues(self, session_id: str) -> list[DeveloperIssue]:
        return self._issues.list_issues(session_id)

    def update_issue_status(self, issue_id: str, status: IssueStatus) -> DeveloperIssue:
        return self._issues.update_issue_status(issue_id, status)

    # ------------------------------------------------------------------
    # Pull Requests
    # ------------------------------------------------------------------

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
    ) -> PullRequest:
        return self._prs.create_pr(
            session_id=session_id,
            title=title,
            source_branch=source_branch,
            target_branch=target_branch,
            description=description,
            reviewers=reviewers,
            merge_strategy=merge_strategy,
            linked_issue_id=linked_issue_id,
        )

    def get_pr(self, pr_id: str) -> PullRequest:
        return self._prs.get_pr(pr_id)

    def list_prs(self, session_id: str) -> list[PullRequest]:
        return self._prs.list_prs(session_id)

    async def merge_pr(self, session_id: str, pr_id: str) -> PullRequest:
        session = self._repo.get_session(session_id)
        return await self._prs.merge_pr(pr_id, session.repo_path)
