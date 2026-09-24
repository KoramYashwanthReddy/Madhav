"""FastAPI router for Module 23 — Developer Agent."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from max.developer.container import get_developer_container
from max.developer.domain.enums import IssuePriority, MergeStrategy, WorkflowType
from max.developer.domain.exceptions import (
    DevPRNotFoundError,
    DevSessionNotFoundError,
    DevWorkflowNotFoundError,
    PermissionDeniedError,
)
from max.developer.domain.models import (
    DeveloperIssue,
    DeveloperSession,
    DeveloperWorkflow,
    GitStatus,
    PullRequest,
)

router = APIRouter(prefix="/developer", tags=["Developer Agent"])


# ----------------------------------------------------------------------
# Request Schemas
# ----------------------------------------------------------------------


class CreateSessionRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute filesystem path to Git repository")
    owner_id: str = Field(default="user_default", description="Owner identifier")


class CreateBranchRequest(BaseModel):
    branch_name: str = Field(..., description="Branch name to create")
    start_point: str = Field(default="", description="Optional start commit/branch")


class CheckoutBranchRequest(BaseModel):
    branch_name: str = Field(..., description="Branch name to checkout")


class CommitRequest(BaseModel):
    message: str = Field(..., description="Commit message")
    paths: list[str] | None = Field(default=None, description="Optional paths to stage")


class PushRequest(BaseModel):
    remote: str = Field(default="origin", description="Remote name")
    branch: str = Field(default="", description="Branch name")
    force: bool = Field(default=False, description="Force push")


class PullRequestParams(BaseModel):
    remote: str = Field(default="origin", description="Remote name")
    branch: str = Field(default="", description="Branch name")


class StartWorkflowRequest(BaseModel):
    workflow_type: WorkflowType = Field(..., description="Type of workflow")
    objective: str = Field(..., description="Workflow objective statement")
    branch_name: str | None = Field(default=None, description="Optional target branch name")
    linked_issue_id: str | None = Field(default=None, description="Optional linked issue ID")


class AdvanceWorkflowRequest(BaseModel):
    commit_message: str = Field(default="", description="Commit message for coding/commit step")
    coding_session_id: str | None = Field(
        default=None, description="Coding Session ID from Module 22"
    )
    tag_name: str | None = Field(default=None, description="Tag name for release step")


class CreateIssueRequest(BaseModel):
    title: str = Field(..., description="Issue title")
    description: str = Field(default="", description="Issue description")
    priority: IssuePriority = Field(default=IssuePriority.MEDIUM, description="Issue priority")
    labels: list[str] | None = Field(default=None, description="Labels list")
    assignee: str | None = Field(default=None, description="Assignee name")


class CreatePRRequest(BaseModel):
    title: str = Field(..., description="PR title")
    source_branch: str = Field(..., description="Source feature/fix branch")
    target_branch: str = Field(..., description="Target base branch")
    description: str = Field(default="", description="PR description")
    reviewers: list[str] | None = Field(default=None, description="Reviewers list")
    merge_strategy: MergeStrategy = Field(
        default=MergeStrategy.MERGE_COMMIT, description="Merge strategy"
    )
    linked_issue_id: str | None = Field(default=None, description="Linked issue ID")


# ----------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, Any]:
    """Return Developer Agent subsystem health status."""
    container = get_developer_container()
    return {
        "status": "healthy",
        "subsystem": "developer_agent",
        "enabled": container.settings.enabled,
    }


@router.post("/sessions", response_model=DeveloperSession, status_code=status.HTTP_201_CREATED)
async def open_session(req: CreateSessionRequest) -> DeveloperSession:
    """Open a Developer Session for a target repository."""
    container = get_developer_container()
    try:
        return await container.service.open_session(req.repo_path, owner_id=req.owner_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions", response_model=list[DeveloperSession])
async def list_sessions(owner_id: str | None = Query(default=None)) -> list[DeveloperSession]:
    """List active developer sessions."""
    container = get_developer_container()
    return container.service.list_sessions(owner_id=owner_id)


@router.get("/sessions/{session_id}", response_model=DeveloperSession)
async def get_session(session_id: str) -> DeveloperSession:
    """Get details of a developer session."""
    container = get_developer_container()
    try:
        return container.service.get_session(session_id)
    except DevSessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Developer session '{session_id}' not found.")


@router.delete("/sessions/{session_id}", status_code=status.HTTP_200_OK)
async def close_session(session_id: str) -> dict[str, str]:
    """Close a developer session."""
    container = get_developer_container()
    try:
        container.service.close_session(session_id)
        return {"session_id": session_id, "status": "CLOSED"}
    except DevSessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Developer session '{session_id}' not found.")


@router.get("/sessions/{session_id}/status", response_model=GitStatus)
async def get_git_status(session_id: str) -> GitStatus:
    """Get Git repository status for session."""
    container = get_developer_container()
    try:
        return await container.service.get_git_status(session_id)
    except DevSessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Developer session '{session_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/{session_id}/branches", status_code=status.HTTP_201_CREATED)
async def create_branch(session_id: str, req: CreateBranchRequest) -> dict[str, str]:
    """Create a new branch and checkout."""
    container = get_developer_container()
    try:
        return await container.service.create_branch(
            session_id, req.branch_name, req.start_point
        )
    except DevSessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Developer session '{session_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/sessions/{session_id}/branches/{branch_name}/checkout", status_code=status.HTTP_200_OK
)
async def checkout_branch(session_id: str, branch_name: str) -> dict[str, str]:
    """Checkout an existing branch."""
    container = get_developer_container()
    try:
        return await container.service.checkout_branch(session_id, branch_name)
    except DevSessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Developer session '{session_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{session_id}/log", response_model=list[dict[str, Any]])
async def get_git_log(
    session_id: str, max_count: int = Query(default=20, ge=1, le=100)
) -> list[dict[str, Any]]:
    """Retrieve Git commit log for session repository."""
    container = get_developer_container()
    try:
        return await container.service.get_log(session_id, max_count=max_count)
    except DevSessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Developer session '{session_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/{session_id}/commit", status_code=status.HTTP_200_OK)
async def stage_and_commit(session_id: str, req: CommitRequest) -> dict[str, str]:
    """Stage changes and create a Git commit."""
    container = get_developer_container()
    try:
        return await container.service.stage_and_commit(session_id, req.message, paths=req.paths)
    except DevSessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Developer session '{session_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/{session_id}/push", status_code=status.HTTP_200_OK)
async def push(session_id: str, req: PushRequest) -> dict[str, str]:
    """Push commits to remote."""
    container = get_developer_container()
    try:
        return await container.service.push(
            session_id, remote=req.remote, branch=req.branch, force=req.force
        )
    except DevSessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Developer session '{session_id}' not found.")
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/{session_id}/pull", status_code=status.HTTP_200_OK)
async def pull(session_id: str, req: PullRequestParams) -> dict[str, str]:
    """Pull changes from remote."""
    container = get_developer_container()
    try:
        return await container.service.pull(session_id, remote=req.remote, branch=req.branch)
    except DevSessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Developer session '{session_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/sessions/{session_id}/workflows",
    response_model=DeveloperWorkflow,
    status_code=status.HTTP_201_CREATED,
)
async def start_workflow(session_id: str, req: StartWorkflowRequest) -> DeveloperWorkflow:
    """Start a multi-step developer workflow."""
    container = get_developer_container()
    try:
        return container.service.start_workflow(
            session_id=session_id,
            workflow_type=req.workflow_type,
            objective=req.objective,
            branch_name=req.branch_name,
            linked_issue_id=req.linked_issue_id,
        )
    except DevSessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Developer session '{session_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/sessions/{session_id}/workflows/{workflow_id}",
    response_model=DeveloperWorkflow,
)
async def get_workflow(session_id: str, workflow_id: str) -> DeveloperWorkflow:
    """Get status of a developer workflow."""
    container = get_developer_container()
    try:
        return container.service.get_workflow(workflow_id)
    except DevWorkflowNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")


@router.post(
    "/sessions/{session_id}/workflows/{workflow_id}/advance",
    response_model=DeveloperWorkflow,
)
async def advance_workflow(
    session_id: str, workflow_id: str, req: AdvanceWorkflowRequest
) -> DeveloperWorkflow:
    """Advance workflow to next state."""
    container = get_developer_container()
    try:
        return await container.service.advance_workflow(
            workflow_id=workflow_id,
            commit_message=req.commit_message,
            coding_session_id=req.coding_session_id,
            tag_name=req.tag_name,
        )
    except DevWorkflowNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{session_id}/issues", response_model=list[DeveloperIssue])
async def list_issues(session_id: str) -> list[DeveloperIssue]:
    """List issues linked to session."""
    container = get_developer_container()
    return container.service.list_issues(session_id)


@router.post(
    "/sessions/{session_id}/issues",
    response_model=DeveloperIssue,
    status_code=status.HTTP_201_CREATED,
)
async def create_issue(session_id: str, req: CreateIssueRequest) -> DeveloperIssue:
    """Create a new developer issue."""
    container = get_developer_container()
    try:
        return container.service.create_issue(
            session_id=session_id,
            title=req.title,
            description=req.description,
            priority=req.priority,
            labels=req.labels,
            assignee=req.assignee,
        )
    except DevSessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Developer session '{session_id}' not found.")


@router.get("/sessions/{session_id}/prs", response_model=list[PullRequest])
async def list_prs(session_id: str) -> list[PullRequest]:
    """List PRs linked to session."""
    container = get_developer_container()
    return container.service.list_prs(session_id)


@router.post(
    "/sessions/{session_id}/prs",
    response_model=PullRequest,
    status_code=status.HTTP_201_CREATED,
)
async def create_pr(session_id: str, req: CreatePRRequest) -> PullRequest:
    """Create a pull request."""
    container = get_developer_container()
    try:
        return container.service.create_pr(
            session_id=session_id,
            title=req.title,
            source_branch=req.source_branch,
            target_branch=req.target_branch,
            description=req.description,
            reviewers=req.reviewers,
            merge_strategy=req.merge_strategy,
            linked_issue_id=req.linked_issue_id,
        )
    except DevSessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Developer session '{session_id}' not found.")


@router.post("/sessions/{session_id}/prs/{pr_id}/merge", response_model=PullRequest)
async def merge_pr(session_id: str, pr_id: str) -> PullRequest:
    """Merge a pull request into target branch."""
    container = get_developer_container()
    try:
        return await container.service.merge_pr(session_id, pr_id)
    except DevPRNotFoundError:
        raise HTTPException(status_code=404, detail=f"Pull request '{pr_id}' not found.")
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
