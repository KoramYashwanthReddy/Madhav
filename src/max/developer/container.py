"""Dependency injection container for Module 23 — Developer Agent."""

import logging
from typing import Any

from max.config.settings import get_settings
from max.developer.repositories.repositories import (
    DevAuditRepository,
    DevIssueRepository,
    DevPRRepository,
    DevSessionRepository,
    DevWorkflowRepository,
)
from max.developer.security.git_policy import GitOperationPolicy
from max.developer.services.developer_service import DeveloperService
from max.developer.services.git_service import GitService
from max.developer.services.issue_service import IssueService
from max.developer.services.pr_service import PRService
from max.developer.services.repo_service import RepoService
from max.developer.services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)


class DeveloperContainer:
    """Dependency injection container for the Developer Agent subsystem."""

    def __init__(
        self,
        gate: Any | None = None,
        terminal_service: Any | None = None,
    ) -> None:
        cfg = get_settings().developer_agent
        self.settings = cfg

        # Policy & Repositories
        self.git_policy = GitOperationPolicy(protected_branches=cfg.protected_branches)
        self.session_repo = DevSessionRepository()
        self.workflow_repo = DevWorkflowRepository()
        self.issue_repo = DevIssueRepository()
        self.pr_repo = DevPRRepository()
        self.audit_repo = DevAuditRepository()

        # Services
        self.git_service = GitService(
            gate=gate,
            terminal_service=terminal_service,
            policy=self.git_policy,
        )
        self.repo_service = RepoService(
            session_repo=self.session_repo,
            audit_repo=self.audit_repo,
            git_service=self.git_service,
        )
        self.issue_service = IssueService(
            session_repo=self.session_repo,
            issue_repo=self.issue_repo,
            audit_repo=self.audit_repo,
        )
        self.pr_service = PRService(
            session_repo=self.session_repo,
            pr_repo=self.pr_repo,
            audit_repo=self.audit_repo,
            git_service=self.git_service,
        )
        self.workflow_service = WorkflowService(
            session_repo=self.session_repo,
            workflow_repo=self.workflow_repo,
            audit_repo=self.audit_repo,
            git_service=self.git_service,
            pr_service=self.pr_service,
        )

        # Master Service Facade
        self.service = DeveloperService(
            repo_service=self.repo_service,
            issue_service=self.issue_service,
            pr_service=self.pr_service,
            workflow_service=self.workflow_service,
            git_service=self.git_service,
        )


_container_instance: DeveloperContainer | None = None


def get_developer_container(
    gate: Any | None = None,
    terminal_service: Any | None = None,
) -> DeveloperContainer:
    """Retrieve or initialize the global DeveloperContainer instance."""
    global _container_instance
    if _container_instance is None:
        _container_instance = DeveloperContainer(gate=gate, terminal_service=terminal_service)
    return _container_instance


def reset_developer_container() -> None:
    """Reset the global DeveloperContainer instance (used for test isolation)."""
    global _container_instance
    _container_instance = None
