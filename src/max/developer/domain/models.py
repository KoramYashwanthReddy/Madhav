"""Domain models for Module 23 — Developer Agent."""

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from max.developer.domain.enums import (
    CIRunStatus,
    DevSessionStatus,
    IssuePriority,
    IssueStatus,
    MergeStrategy,
    PRStatus,
    WorkflowStatus,
    WorkflowStep,
    WorkflowType,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Git Primitives
# ---------------------------------------------------------------------------


class GitRemote(BaseModel):
    """Represents a configured Git remote."""

    name: str = Field(description="Remote alias name (e.g. 'origin')")
    url: str = Field(description="Remote URL")
    fetch_url: str | None = Field(default=None, description="Fetch URL (if different)")


class GitBranch(BaseModel):
    """Represents a local or remote Git branch."""

    name: str = Field(description="Branch name")
    is_current: bool = Field(default=False, description="Whether this is the active checkout")
    is_remote: bool = Field(default=False, description="Whether this is a remote tracking branch")
    upstream: str | None = Field(default=None, description="Upstream tracking branch name")
    ahead: int = Field(default=0, description="Commits ahead of upstream")
    behind: int = Field(default=0, description="Commits behind upstream")


class GitCommit(BaseModel):
    """Structured representation of a Git commit."""

    sha: str = Field(description="Full commit SHA")
    short_sha: str = Field(description="Abbreviated commit SHA (7 chars)")
    message: str = Field(description="Commit message (first line)")
    author_name: str = Field(default="", description="Author display name")
    author_email: str = Field(default="", description="Author email address")
    committed_at: datetime = Field(default_factory=_utc_now)


class GitStatusEntry(BaseModel):
    """Single file entry from git status output."""

    path: str = Field(description="Relative file path")
    status_code: str = Field(description="Git status code (e.g. 'M', 'A', '??')")
    staged: bool = Field(default=False, description="Whether the change is staged")


class GitStatus(BaseModel):
    """Repository working-tree status summary."""

    branch: str = Field(default="", description="Current branch name")
    is_clean: bool = Field(default=True, description="True when no uncommitted changes")
    entries: list[GitStatusEntry] = Field(default_factory=list)
    ahead: int = Field(default=0, description="Commits ahead of upstream")
    behind: int = Field(default=0, description="Commits behind upstream")
    raw_output: str = Field(default="", description="Raw git status output for audit")


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class Repository(BaseModel):
    """Local Git repository metadata."""

    id: str = Field(default_factory=lambda: f"repo_{uuid.uuid4().hex[:10]}")
    path: str = Field(description="Absolute filesystem path to repository root")
    name: str = Field(default="", description="Repository name (directory basename)")
    default_branch: str = Field(default="main", description="Configured default/main branch")
    current_branch: str = Field(default="", description="Currently checked-out branch")
    remotes: list[GitRemote] = Field(default_factory=list)
    is_valid_git_repo: bool = Field(default=False)
    discovered_at: datetime = Field(default_factory=_utc_now)


# ---------------------------------------------------------------------------
# Issue Tracker
# ---------------------------------------------------------------------------


class DeveloperIssue(BaseModel):
    """Issue tracker item (in-memory; GitHub integration is a future layer)."""

    id: str = Field(default_factory=lambda: f"iss_{uuid.uuid4().hex[:10]}")
    session_id: str = Field(description="Owning developer session")
    title: str = Field(description="Issue title")
    description: str = Field(default="", description="Issue description")
    status: IssueStatus = Field(default=IssueStatus.OPEN)
    priority: IssuePriority = Field(default=IssuePriority.MEDIUM)
    labels: list[str] = Field(default_factory=list)
    assignee: str | None = Field(default=None)
    linked_branch: str | None = Field(default=None, description="Branch created for this issue")
    linked_workflow_id: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


# ---------------------------------------------------------------------------
# Pull Request
# ---------------------------------------------------------------------------


class PullRequest(BaseModel):
    """Pull request record with lifecycle state machine."""

    id: str = Field(default_factory=lambda: f"pr_{uuid.uuid4().hex[:10]}")
    session_id: str = Field(description="Owning developer session")
    title: str = Field(description="PR title")
    description: str = Field(default="", description="PR body/description")
    source_branch: str = Field(description="Branch being merged")
    target_branch: str = Field(description="Branch receiving the merge")
    status: PRStatus = Field(default=PRStatus.DRAFT)
    merge_strategy: MergeStrategy = Field(default=MergeStrategy.MERGE_COMMIT)
    reviewers: list[str] = Field(default_factory=list)
    linked_issue_id: str | None = Field(default=None)
    linked_workflow_id: str | None = Field(default=None)
    merged_sha: str | None = Field(default=None, description="Merge commit SHA after merge")
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
    merged_at: datetime | None = Field(default=None)


# ---------------------------------------------------------------------------
# CI/CD
# ---------------------------------------------------------------------------


class CIRun(BaseModel):
    """Represents a CI/CD pipeline run record."""

    id: str = Field(default_factory=lambda: f"ci_{uuid.uuid4().hex[:8]}")
    pr_id: str | None = Field(default=None, description="Associated PR")
    branch: str = Field(description="Branch that triggered the run")
    commit_sha: str = Field(default="", description="Commit SHA that triggered the run")
    status: CIRunStatus = Field(default=CIRunStatus.UNKNOWN)
    pipeline_url: str | None = Field(default=None)
    started_at: datetime = Field(default_factory=_utc_now)
    completed_at: datetime | None = Field(default=None)
    conclusion: str | None = Field(default=None, description="Final result string from CI provider")


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


class WorkflowStepRecord(BaseModel):
    """Record of a single executed workflow step."""

    step: WorkflowStep
    status: str = Field(default="PENDING", description="PENDING | SUCCESS | FAILED | SKIPPED")
    message: str = Field(default="")
    executed_at: datetime | None = Field(default=None)
    details: dict[str, Any] = Field(default_factory=dict)


class DeveloperWorkflow(BaseModel):
    """Orchestration record for a multi-step developer workflow."""

    id: str = Field(default_factory=lambda: f"wf_{uuid.uuid4().hex[:12]}")
    session_id: str = Field(description="Owning developer session")
    workflow_type: WorkflowType = Field(description="Workflow category")
    objective: str = Field(description="High-level description of what this workflow accomplishes")
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING)
    current_step: WorkflowStep = Field(default=WorkflowStep.INIT)
    steps: list[WorkflowStepRecord] = Field(default_factory=list)
    branch_name: str | None = Field(default=None, description="Branch created for this workflow")
    coding_session_id: str | None = Field(default=None, description="Module 22 session ID")
    pr_id: str | None = Field(default=None, description="PR created for this workflow")
    linked_issue_id: str | None = Field(default=None)
    error_message: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
    completed_at: datetime | None = Field(default=None)


# ---------------------------------------------------------------------------
# Developer Session
# ---------------------------------------------------------------------------


class DeveloperSession(BaseModel):
    """Root session context tying together repository, workflows, issues, and PRs."""

    id: str = Field(default_factory=lambda: f"dses_{uuid.uuid4().hex[:12]}")
    repo_path: str = Field(description="Absolute path to the repository root")
    owner_id: str = Field(default="user_default", description="Requesting user or agent ID")
    status: DevSessionStatus = Field(default=DevSessionStatus.OPEN)
    repository: Repository | None = Field(default=None, description="Populated on session open")
    active_workflow_id: str | None = Field(default=None)
    workflow_ids: list[str] = Field(default_factory=list)
    issue_ids: list[str] = Field(default_factory=list)
    pr_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
    closed_at: datetime | None = Field(default=None)


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


class DevAuditEvent(BaseModel):
    """Immutable audit log record for Developer Agent operations."""

    id: str = Field(default_factory=lambda: f"daud_{uuid.uuid4().hex[:10]}")
    timestamp: datetime = Field(default_factory=_utc_now)
    session_id: str
    event_type: str = Field(description="Audit event type string")
    owner_id: str = Field(default="system")
    details: dict[str, Any] = Field(default_factory=dict)
