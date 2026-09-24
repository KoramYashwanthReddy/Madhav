"""Workflow service for Module 23 — Developer Agent.

Orchestrates multi-step developer workflows as a deterministic state machine.
Coding work is delegated exclusively to Module 22 (CodingService).
"""

import logging
from datetime import datetime, timezone

from max.developer.domain.enums import (
    MergeStrategy,
    PRStatus,
    WorkflowStatus,
    WorkflowStep,
    WorkflowType,
)
from max.developer.domain.exceptions import (
    WorkflowExecutionError,
    WorkflowTransitionError,
)
from max.developer.domain.models import (
    DevAuditEvent,
    DeveloperWorkflow,
    WorkflowStepRecord,
)
from max.developer.repositories.repositories import (
    DevAuditRepository,
    DevSessionRepository,
    DevWorkflowRepository,
)
from max.developer.services.git_service import GitService
from max.developer.services.pr_service import PRService

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# Ordered step sequences per workflow type
_WORKFLOW_STEPS: dict[WorkflowType, list[WorkflowStep]] = {
    WorkflowType.FEATURE: [
        WorkflowStep.INIT,
        WorkflowStep.CREATE_BRANCH,
        WorkflowStep.DELEGATE_CODING,
        WorkflowStep.STAGE_AND_COMMIT,
        WorkflowStep.PUSH,
        WorkflowStep.OPEN_PR,
        WorkflowStep.AWAIT_REVIEW,
        WorkflowStep.DONE,
    ],
    WorkflowType.BUGFIX: [
        WorkflowStep.INIT,
        WorkflowStep.CREATE_BRANCH,
        WorkflowStep.DELEGATE_CODING,
        WorkflowStep.STAGE_AND_COMMIT,
        WorkflowStep.PUSH,
        WorkflowStep.OPEN_PR,
        WorkflowStep.DONE,
    ],
    WorkflowType.HOTFIX: [
        WorkflowStep.INIT,
        WorkflowStep.CREATE_BRANCH,
        WorkflowStep.DELEGATE_CODING,
        WorkflowStep.STAGE_AND_COMMIT,
        WorkflowStep.PUSH,
        WorkflowStep.OPEN_PR,
        WorkflowStep.MERGE,
        WorkflowStep.DONE,
    ],
    WorkflowType.RELEASE: [
        WorkflowStep.INIT,
        WorkflowStep.CREATE_BRANCH,
        WorkflowStep.TAG_RELEASE,
        WorkflowStep.PUSH,
        WorkflowStep.OPEN_PR,
        WorkflowStep.AWAIT_REVIEW,
        WorkflowStep.MERGE,
        WorkflowStep.CLEANUP,
        WorkflowStep.DONE,
    ],
    WorkflowType.REFACTOR: [
        WorkflowStep.INIT,
        WorkflowStep.CREATE_BRANCH,
        WorkflowStep.DELEGATE_CODING,
        WorkflowStep.STAGE_AND_COMMIT,
        WorkflowStep.PUSH,
        WorkflowStep.OPEN_PR,
        WorkflowStep.DONE,
    ],
    WorkflowType.CUSTOM: [
        WorkflowStep.INIT,
        WorkflowStep.DONE,
    ],
}


class WorkflowService:
    """Orchestrates multi-step developer workflows as a state machine.

    Coding work is delegated to Module 22 by storing a coding_session_id
    reference on the workflow. This service does NOT call Module 22 directly
    to maintain module independence — the API layer or DeveloperService
    coordinates M22 calls and then advances the workflow.
    """

    def __init__(
        self,
        session_repo: DevSessionRepository,
        workflow_repo: DevWorkflowRepository,
        audit_repo: DevAuditRepository,
        git_service: GitService,
        pr_service: PRService,
        default_branch: str = "main",
        max_workflows_per_session: int = 10,
    ) -> None:
        self._session_repo = session_repo
        self._workflow_repo = workflow_repo
        self._audit_repo = audit_repo
        self._git = git_service
        self._pr_service = pr_service
        self._default_branch = default_branch
        self._max_workflows = max_workflows_per_session

    def start_workflow(
        self,
        session_id: str,
        workflow_type: WorkflowType,
        objective: str,
        branch_name: str | None = None,
        linked_issue_id: str | None = None,
    ) -> DeveloperWorkflow:
        """Create a new workflow in PENDING state with initialized step records."""
        session = self._session_repo.get(session_id)

        if len(session.workflow_ids) >= self._max_workflows:
            raise WorkflowExecutionError(
                f"Session '{session_id}' has reached the maximum workflow limit ({self._max_workflows}).",
                details={"session_id": session_id, "limit": self._max_workflows},
            )

        steps = _WORKFLOW_STEPS.get(workflow_type, _WORKFLOW_STEPS[WorkflowType.CUSTOM])
        step_records = [WorkflowStepRecord(step=s) for s in steps]

        workflow = DeveloperWorkflow(
            session_id=session_id,
            workflow_type=workflow_type,
            objective=objective,
            status=WorkflowStatus.PENDING,
            current_step=WorkflowStep.INIT,
            steps=step_records,
            branch_name=branch_name,
            linked_issue_id=linked_issue_id,
        )
        self._workflow_repo.save(workflow)
        session.workflow_ids.append(workflow.id)
        session.active_workflow_id = workflow.id
        self._session_repo.save(session)

        self._audit_repo.append(
            DevAuditEvent(
                session_id=session_id,
                event_type="WORKFLOW_STARTED",
                owner_id=session.owner_id,
                details={
                    "workflow_id": workflow.id,
                    "type": workflow_type.value,
                    "objective": objective,
                },
            )
        )
        logger.info("Workflow %s started in session %s (%s)", workflow.id, session_id, workflow_type.value)
        return workflow

    def get_workflow(self, workflow_id: str) -> DeveloperWorkflow:
        """Retrieve a workflow by ID."""
        return self._workflow_repo.get(workflow_id)

    def list_workflows(self, session_id: str) -> list[DeveloperWorkflow]:
        """List all workflows for a session."""
        return self._workflow_repo.list_for_session(session_id)

    async def advance_workflow(
        self,
        workflow_id: str,
        commit_message: str = "",
        coding_session_id: str | None = None,
        tag_name: str | None = None,
    ) -> DeveloperWorkflow:
        """Advance the workflow to its next step and execute the step action.

        This is the central state machine driver. Each call advances by one
        step. The caller is responsible for ensuring prerequisite state is
        ready (e.g. coding session completed) before calling advance.
        """
        workflow = self._workflow_repo.get(workflow_id)
        session = self._session_repo.get(workflow.session_id)
        repo_path = session.repo_path

        if coding_session_id:
            workflow.coding_session_id = coding_session_id

        if workflow.status in {WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED}:
            raise WorkflowTransitionError(
                f"Workflow '{workflow_id}' is already in terminal state '{workflow.status.value}'.",
                details={"workflow_id": workflow_id, "status": workflow.status.value},
            )

        # Identify current step index and next step
        step_names = [r.step for r in workflow.steps]
        try:
            current_idx = step_names.index(workflow.current_step)
        except ValueError:
            current_idx = 0

        next_idx = current_idx + 1
        if next_idx >= len(workflow.steps):
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = _utc_now()
            self._workflow_repo.save(workflow)
            return workflow

        next_step = workflow.steps[next_idx].step
        workflow.current_step = next_step
        workflow.status = WorkflowStatus.IN_PROGRESS
        workflow.updated_at = _utc_now()

        # Mark current step as in-progress
        workflow.steps[next_idx].status = "IN_PROGRESS"
        workflow.steps[next_idx].executed_at = _utc_now()

        # Mark previous step done
        workflow.steps[current_idx].status = "SUCCESS"

        # Persist optimistic state
        self._workflow_repo.save(workflow)

        try:
            await self._execute_step(
                workflow=workflow,
                step=next_step,
                repo_path=repo_path,
                session=session,
                commit_message=commit_message,
                coding_session_id=coding_session_id,
                tag_name=tag_name,
            )
            workflow.steps[next_idx].status = "SUCCESS"
        except Exception as exc:
            workflow.steps[next_idx].status = "FAILED"
            workflow.steps[next_idx].message = str(exc)
            workflow.status = WorkflowStatus.FAILED
            workflow.error_message = str(exc)
            self._workflow_repo.save(workflow)
            self._audit_repo.append(
                DevAuditEvent(
                    session_id=workflow.session_id,
                    event_type="WORKFLOW_STEP_FAILED",
                    owner_id=session.owner_id,
                    details={"workflow_id": workflow_id, "step": next_step.value, "error": str(exc)},
                )
            )
            raise WorkflowExecutionError(
                f"Workflow step '{next_step.value}' failed: {exc}",
                details={"workflow_id": workflow_id, "step": next_step.value},
            ) from exc

        # Check if we just completed the workflow
        if next_step == WorkflowStep.DONE:
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = _utc_now()

        workflow.updated_at = _utc_now()
        self._workflow_repo.save(workflow)
        self._audit_repo.append(
            DevAuditEvent(
                session_id=workflow.session_id,
                event_type="WORKFLOW_STEP_COMPLETED",
                owner_id=session.owner_id,
                details={"workflow_id": workflow_id, "step": next_step.value},
            )
        )
        return workflow

    async def _execute_step(
        self,
        workflow: "DeveloperWorkflow",
        step: WorkflowStep,
        repo_path: str,
        session: object,
        commit_message: str = "",
        coding_session_id: str | None = None,
        tag_name: str | None = None,
    ) -> None:
        """Execute the action for a single workflow step."""
        if step == WorkflowStep.INIT:
            # Nothing to do — init is a marker step
            pass

        elif step == WorkflowStep.CREATE_BRANCH:
            if workflow.branch_name:
                await self._git.create_and_checkout(repo_path, workflow.branch_name)

        elif step == WorkflowStep.DELEGATE_CODING:
            # Record coding session ID if provided by caller (API layer coordinates M22)
            if coding_session_id:
                workflow.coding_session_id = coding_session_id

        elif step == WorkflowStep.STAGE_AND_COMMIT:
            msg = commit_message or f"{workflow.workflow_type.value.lower()}: {workflow.objective[:72]}"
            await self._git.add(repo_path)
            await self._git.commit(repo_path, msg)

        elif step == WorkflowStep.PUSH:
            branch = workflow.branch_name or ""
            await self._git.push(repo_path, branch=branch, set_upstream=True)

        elif step == WorkflowStep.OPEN_PR:
            default_branch = getattr(session, "repository", None)
            if default_branch:
                default_branch = getattr(default_branch, "default_branch", self._default_branch)
            else:
                default_branch = self._default_branch
            pr = self._pr_service.create_pr(
                session_id=workflow.session_id,
                title=f"{workflow.workflow_type.value}: {workflow.objective[:80]}",
                source_branch=workflow.branch_name or "",
                target_branch=default_branch,
                description=workflow.objective,
                linked_workflow_id=workflow.id,
                linked_issue_id=workflow.linked_issue_id,
            )
            self._pr_service.open_pr(pr.id)
            workflow.pr_id = pr.id

        elif step == WorkflowStep.AWAIT_REVIEW:
            # Mark PR as awaiting review
            if workflow.pr_id:
                pr = self._pr_service.get_pr(workflow.pr_id)
                if pr.status == PRStatus.OPEN:
                    self._pr_service.request_review(workflow.pr_id, reviewers=[])
            workflow.status = WorkflowStatus.AWAITING_APPROVAL

        elif step == WorkflowStep.MERGE:
            if workflow.pr_id:
                await self._pr_service.merge_pr(workflow.pr_id, repo_path)

        elif step == WorkflowStep.TAG_RELEASE:
            name = tag_name or f"v{workflow.objective[:20].replace(' ', '-')}"
            await self._git.create_tag(repo_path, name, message=workflow.objective)

        elif step == WorkflowStep.CLEANUP:
            if workflow.branch_name and workflow.branch_name not in ("main", "master", "release"):
                try:
                    await self._git.delete_branch(repo_path, workflow.branch_name)
                except Exception:
                    pass  # Cleanup failures are non-fatal

        elif step == WorkflowStep.DONE:
            pass  # Terminal marker step

    def cancel_workflow(self, workflow_id: str) -> DeveloperWorkflow:
        """Cancel a workflow."""
        workflow = self._workflow_repo.get(workflow_id)
        workflow.status = WorkflowStatus.CANCELLED
        workflow.updated_at = _utc_now()
        self._workflow_repo.save(workflow)
        return workflow
