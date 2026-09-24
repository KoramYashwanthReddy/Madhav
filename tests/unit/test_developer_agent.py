"""Comprehensive unit test suite for Module 23 — Developer Agent."""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from max.api.router import register_routers
from max.developer.container import get_developer_container, reset_developer_container
from max.developer.domain.enums import (
    CIRunStatus,
    DevSessionStatus,
    GitOperationRisk,
    IssuePriority,
    IssueStatus,
    MergeStrategy,
    PRStatus,
    WorkflowStep,
    WorkflowType,
)
from max.developer.domain.exceptions import (
    DevIssueNotFoundError,
    DevPRNotFoundError,
    DevSessionNotFoundError,
    DevWorkflowNotFoundError,
    PermissionDeniedError,
)
from max.developer.domain.models import (
    DevAuditEvent,
    DeveloperIssue,
    DeveloperSession,
    DeveloperWorkflow,
    GitBranch,
    GitCommit,
    GitStatus,
    PullRequest,
)
from max.developer.repositories.repositories import (
    DevAuditRepository,
    DevSessionRepository,
    DevWorkflowRepository,
)
from max.developer.security.git_policy import GitOperationPolicy
from max.developer.services.git_service import GitService
from max.developer.services.issue_service import IssueService
from max.developer.services.pr_service import PRService
from max.developer.services.repo_service import RepoService
from max.developer.services.workflow_service import WorkflowService
from max.terminal.domain.models import CommandResult


@pytest.fixture(autouse=True)
def cleanup_container():
    reset_developer_container()
    yield
    reset_developer_container()


@pytest.fixture
def temp_git_repo():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy git dir
        os.makedirs(os.path.join(tmpdir, ".git"), exist_ok=True)
        readme = os.path.join(tmpdir, "README.md")
        with open(readme, "w", encoding="utf-8") as f:
            f.write("# Test Repo\n")
        yield tmpdir


@pytest.fixture
def test_app():
    app = FastAPI()
    register_routers(app)
    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


# ----------------------------------------------------------------------
# 1. DOMAIN MODELS & ENUMS
# ----------------------------------------------------------------------


def test_domain_enums_and_models():
    assert DevSessionStatus.OPEN == "OPEN"
    assert WorkflowType.FEATURE == "FEATURE"
    assert GitOperationRisk.CRITICAL == "CRITICAL"

    session = DeveloperSession(repo_path="/tmp/repo")
    assert session.status == DevSessionStatus.OPEN
    assert session.id.startswith("dses_")

    issue = DeveloperIssue(session_id=session.id, title="Test issue")
    assert issue.status == IssueStatus.OPEN
    assert issue.priority == IssuePriority.MEDIUM

    pr = PullRequest(
        session_id=session.id,
        title="Test PR",
        source_branch="feature",
        target_branch="main",
    )
    assert pr.status == PRStatus.DRAFT
    assert pr.merge_strategy == MergeStrategy.MERGE_COMMIT


# ----------------------------------------------------------------------
# 2. REPOSITORIES
# ----------------------------------------------------------------------


def test_developer_repositories():
    sess_repo = DevSessionRepository()
    wf_repo = DevWorkflowRepository()
    audit_repo = DevAuditRepository()

    sess = DeveloperSession(repo_path="/path/1")
    sess_repo.save(sess)
    assert sess_repo.get(sess.id).repo_path == "/path/1"
    assert len(sess_repo.list_all()) == 1

    wf = DeveloperWorkflow(session_id=sess.id, workflow_type=WorkflowType.FEATURE, objective="Add feature")
    wf_repo.save(wf)
    assert wf_repo.get(wf.id).objective == "Add feature"
    assert len(wf_repo.list_for_session(sess.id)) == 1

    event = DevAuditEvent(session_id=sess.id, event_type="git_push", owner_id="user_default", details={"branch": "main"})
    audit_repo.append(event)
    assert event.event_type == "git_push"
    assert len(audit_repo.list_for_session(sess.id)) == 1


# ----------------------------------------------------------------------
# 3. SECURITY POLICY — GIT OPERATION RISK
# ----------------------------------------------------------------------


def test_git_operation_policy():
    policy = GitOperationPolicy(protected_branches=["main", "master"])

    verdict_status = policy.evaluate("status")
    assert verdict_status.risk == GitOperationRisk.READ_ONLY
    assert verdict_status.requires_approval is False

    verdict_force_push = policy.evaluate("push", target_branch="feature", force=True)
    assert verdict_force_push.risk == GitOperationRisk.HIGH
    assert verdict_force_push.requires_approval is True

    verdict_delete_protected = policy.evaluate("branch", branch="main", extra_args=["-D"])
    assert verdict_delete_protected.risk == GitOperationRisk.CRITICAL
    assert verdict_delete_protected.requires_approval is True


# ----------------------------------------------------------------------
# 4. GIT SERVICE & PERMISSION GATE INTEGRATION
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_git_service_mocked_terminal():
    mock_terminal = MagicMock()
    mock_res = CommandResult(
        request_id="cmd_123",
        status="COMPLETED",  # type: ignore[arg-type]
        shell="POWERSHELL",  # type: ignore[arg-type]
        command="git status",
        exit_code=0,
        stdout="## main...origin/main\n",
        stderr="",
        duration=0.001,
    )
    mock_terminal.execute_command = AsyncMock(return_value=mock_res)

    git_service = GitService(terminal_service=mock_terminal)

    st = await git_service.status("/tmp/repo")
    assert st.branch == "main"
    assert st.is_clean is True


@pytest.mark.asyncio
async def test_git_service_permission_denied():
    mock_gate = MagicMock()
    mock_decision = MagicMock()
    mock_decision.is_granted = False
    mock_decision.reason = "Destructive git operation forbidden"
    mock_gate.check = MagicMock(return_value=mock_decision)

    policy = GitOperationPolicy(protected_branches=["main"])
    git_service = GitService(gate=mock_gate, policy=policy)

    with pytest.raises(PermissionDeniedError) as exc_info:
        await git_service.push("/tmp/repo", remote="origin", branch="main", force=True)
    assert "forbidden" in str(exc_info.value).lower() or "denied" in str(exc_info.value).lower()


# ----------------------------------------------------------------------
# 5. WORKFLOW STATE MACHINE
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_feature_workflow_lifecycle(temp_git_repo):
    container = get_developer_container()
    service = container.service

    # 1. Open session
    session = await service.open_session(temp_git_repo)
    assert session.status == DevSessionStatus.OPEN

    # 2. Start feature workflow
    wf = service.start_workflow(
        session_id=session.id,
        workflow_type=WorkflowType.FEATURE,
        objective="Add user auth feature",
        branch_name="feature/user-auth",
    )
    assert wf.current_step == WorkflowStep.INIT

    # 3. Advance step 1: INIT -> CREATE_BRANCH
    wf = await service.advance_workflow(wf.id)
    assert wf.current_step == WorkflowStep.CREATE_BRANCH

    # 4. Advance step 2: CREATE_BRANCH -> DELEGATE_CODING
    wf = await service.advance_workflow(wf.id)
    assert wf.current_step == WorkflowStep.DELEGATE_CODING

    # 5. Advance step 3: DELEGATE_CODING -> STAGE_AND_COMMIT
    wf = await service.advance_workflow(wf.id, coding_session_id="coding_sess_999")
    assert wf.current_step == WorkflowStep.STAGE_AND_COMMIT
    assert wf.coding_session_id == "coding_sess_999"


# ----------------------------------------------------------------------
# 6. FASTAPI API ROUTES
# ----------------------------------------------------------------------


def test_api_health(client):
    res = client.get("/api/v1/developer/health")
    assert res.status_code == 200
    assert res.json()["subsystem"] == "developer_agent"


@pytest.mark.asyncio
async def test_api_full_session_and_issue_flow(client, temp_git_repo):
    # 1. Create Session
    res = client.post("/api/v1/developer/sessions", json={"repo_path": temp_git_repo})
    assert res.status_code == 201
    sess_data = res.json()
    session_id = sess_data["id"]

    # 2. Get Session
    get_res = client.get(f"/api/v1/developer/sessions/{session_id}")
    assert get_res.status_code == 200
    assert get_res.json()["repo_path"] == temp_git_repo

    # 3. Create Issue
    issue_payload = {
        "title": "Fix login crash",
        "description": "App crashes when entering invalid email",
        "priority": "HIGH",
    }
    issue_res = client.post(f"/api/v1/developer/sessions/{session_id}/issues", json=issue_payload)
    assert issue_res.status_code == 201
    issue_data = issue_res.json()
    assert issue_data["title"] == "Fix login crash"
    assert issue_data["priority"] == "HIGH"

    # 4. List Issues
    list_iss = client.get(f"/api/v1/developer/sessions/{session_id}/issues")
    assert list_iss.status_code == 200
    assert len(list_iss.json()) == 1

    # 5. Create PR
    pr_payload = {
        "title": "Fix login crash PR",
        "source_branch": "fix/login-crash",
        "target_branch": "main",
        "linked_issue_id": issue_data["id"],
    }
    pr_res = client.post(f"/api/v1/developer/sessions/{session_id}/prs", json=pr_payload)
    assert pr_res.status_code == 201
    pr_data = pr_res.json()
    assert pr_data["title"] == "Fix login crash PR"

    # 6. List PRs
    list_prs = client.get(f"/api/v1/developer/sessions/{session_id}/prs")
    assert list_prs.status_code == 200
    assert len(list_prs.json()) == 1

    # 7. Close Session
    close_res = client.delete(f"/api/v1/developer/sessions/{session_id}")
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "CLOSED"
