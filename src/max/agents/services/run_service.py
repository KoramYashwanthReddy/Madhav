"""AgentRun execution lifecycle service."""

import logging
from datetime import datetime
from typing import Any

from max.agents.domain.agent import PermissionRequestIntent, ToolRequestIntent
from max.agents.domain.enums import (
    AgentEventType,
    AgentExecutionMode,
    AgentRunStatus,
    AgentStatus,
    NextAction,
)
from max.agents.domain.exceptions import (
    AgentInactiveError,
    AgentLimitExceededError,
    AgentNotFoundError,
    AgentRunNotFoundError,
    InvalidRunStateTransitionError,
)
from max.agents.domain.run import AgentFailure, AgentResult, AgentRun
from max.agents.repositories.agent_repository import BaseAgentRepository, MemoryAgentRepository
from max.agents.repositories.run_repository import (
    BaseAgentRunRepository,
    MemoryAgentRunRepository,
)
from max.agents.services.state_machine import AgentRunStateMachine
from max.agents.services.trace_service import AgentTraceService

logger = logging.getLogger(__name__)


class AgentRunService:
    """Service managing AgentRun creation, state machine transitions, retries, and outcomes."""

    def __init__(
        self,
        run_repo: BaseAgentRunRepository | None = None,
        agent_repo: BaseAgentRepository | None = None,
        trace_service: AgentTraceService | None = None,
    ) -> None:
        self.run_repo = run_repo or MemoryAgentRunRepository()
        self.agent_repo = agent_repo or MemoryAgentRepository()
        self.trace_service = trace_service or AgentTraceService()

    @property
    def repository(self) -> BaseAgentRunRepository:
        return self.run_repo

    def create_run(
        self,
        agent_id: str,
        owner_id: str,
        task_id: str | None = None,
        plan_id: str | None = None,
        plan_step_id: str | None = None,
        conversation_id: str | None = None,
        execution_mode: AgentExecutionMode = AgentExecutionMode.DRY_RUN,
        client_request_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentRun:
        """Create a new AgentRun lifecycle instance."""
        agent = self.agent_repo.get_by_id(agent_id)
        if not agent:
            raise AgentNotFoundError(f"Agent '{agent_id}' not found")

        if agent.status != AgentStatus.ACTIVE:
            raise AgentInactiveError(agent_id, agent.status.value)

        # Enforce max concurrent runs limit
        active_count = self.run_repo.count_active_runs_for_agent(agent_id)
        if active_count >= agent.limits.max_concurrent_tasks:
            raise AgentLimitExceededError(
                limit_name="max_concurrent_tasks",
                current_val=active_count + 1,
                max_val=agent.limits.max_concurrent_tasks,
            )

        run_metadata = metadata or {}
        if client_request_id:
            run_metadata["client_request_id"] = client_request_id

        run = AgentRun(
            agent_id=agent_id,
            task_id=task_id,
            plan_id=plan_id,
            plan_step_id=plan_step_id,
            conversation_id=conversation_id,
            owner_id=owner_id,
            status=AgentRunStatus.CREATED,
            execution_mode=execution_mode,
            metadata=run_metadata,
        )
        saved = self.run_repo.save(run)

        self.trace_service.record_event(
            event_type=AgentEventType.RUN_CREATED,
            agent_id=agent_id,
            run_id=saved.run_id,
            task_id=task_id,
            step_id=plan_step_id,
            summary=f"AgentRun '{saved.run_id}' created for agent '{agent.name}'",
        )
        return saved

    def get_run(self, run_id: str) -> AgentRun:
        """Retrieve an AgentRun by ID."""
        run = self.run_repo.get_by_id(run_id)
        if not run:
            raise AgentRunNotFoundError(f"AgentRun '{run_id}' not found.")
        return run

    def start_run(self, run_id: str) -> AgentRun:
        """Start execution lifecycle of a run."""
        run = self.get_run(run_id)
        if run.status == AgentRunStatus.CREATED:
            self.transition_run_status(run_id, AgentRunStatus.INITIALIZING, reason="Initializing run context")
            self.transition_run_status(run_id, AgentRunStatus.READY, reason="Ready for execution")
        return self.transition_run_status(run_id, AgentRunStatus.RUNNING, reason="Run started")

    def pause_run(self, run_id: str) -> AgentRun:
        """Pause a running run."""
        return self.transition_run_status(run_id, AgentRunStatus.PAUSED, reason="Run paused")

    def resume_run(self, run_id: str) -> AgentRun:
        """Resume a paused run."""
        return self.transition_run_status(run_id, AgentRunStatus.RUNNING, reason="Run resumed")

    def cancel_run(self, run_id: str, reason: str = "Cancelled by user") -> AgentRun:
        """Cancel an active run."""
        return self.transition_run_status(run_id, AgentRunStatus.CANCELLED, reason=reason)

    def complete_run(self, run_id: str, result: AgentResult | None = None) -> AgentRun:
        """Complete an active run."""
        res = result or AgentResult(status=AgentRunStatus.COMPLETED, summary="Run completed successfully")
        return self.transition_run_status(run_id, AgentRunStatus.COMPLETED, reason="Run completed", result=res)

    def fail_run(self, run_id: str, failure: AgentFailure | None = None) -> AgentRun:
        """Mark run as failed."""
        fail = failure or AgentFailure(error_code="RUN_FAILED", message="Run execution failed")
        return self.transition_run_status(run_id, AgentRunStatus.FAILED, reason="Run failed", failure=fail)

    def list_runs_for_agent(self, agent_id: str) -> list[AgentRun]:
        """List all runs for an agent."""
        runs, _ = self.list_runs(agent_id=agent_id, limit=500)
        return runs

    def transition_run_status(
        self,
        run_id: str,
        target_status: AgentRunStatus,
        reason: str = "Status transition",
        result: AgentResult | None = None,
        failure: AgentFailure | None = None,
        next_action: NextAction | None = None,
        tool_requests: list[ToolRequestIntent] | None = None,
        permission_requests: list[PermissionRequestIntent] | None = None,
    ) -> AgentRun:
        """Transition AgentRun to a new status using AgentRunStateMachine."""
        run = self.get_run(run_id)
        AgentRunStateMachine.validate_transition(run.status, target_status, reason=reason)

        now = datetime.utcnow()
        updated_dict = run.model_dump()
        updated_dict["status"] = target_status
        updated_dict["updated_at"] = now

        if target_status == AgentRunStatus.RUNNING and run.started_at is None:
            updated_dict["started_at"] = now

        if target_status in (AgentRunStatus.COMPLETED, AgentRunStatus.FAILED, AgentRunStatus.CANCELLED, AgentRunStatus.TIMED_OUT):
            updated_dict["completed_at"] = now

        if result is not None:
            updated_dict["result"] = result
        if failure is not None:
            updated_dict["failure"] = failure
        if next_action is not None:
            updated_dict["next_action"] = next_action
        if tool_requests is not None:
            updated_dict["tool_requests"] = tool_requests
        if permission_requests is not None:
            updated_dict["permission_requests"] = permission_requests

        new_run = AgentRun(**updated_dict)
        saved = self.run_repo.save(new_run)

        event_map = {
            AgentRunStatus.RUNNING: AgentEventType.RUN_STARTED,
            AgentRunStatus.WAITING: AgentEventType.RUN_WAITING,
            AgentRunStatus.COMPLETED: AgentEventType.RUN_COMPLETED,
            AgentRunStatus.FAILED: AgentEventType.RUN_FAILED,
            AgentRunStatus.CANCELLED: AgentEventType.RUN_CANCELLED,
            AgentRunStatus.TIMED_OUT: AgentEventType.RUN_TIMED_OUT,
        }
        event_type = event_map.get(target_status, AgentEventType.RUN_STARTED)

        self.trace_service.record_event(
            event_type=event_type,
            agent_id=saved.agent_id,
            run_id=saved.run_id,
            task_id=saved.task_id,
            step_id=saved.plan_step_id,
            summary=f"AgentRun transition to '{target_status.value}': {reason}",
        )

        logger.info(
            "AgentRun status transition",
            extra={
                "run_id": saved.run_id,
                "agent_id": saved.agent_id,
                "previous_status": run.status.value,
                "new_status": target_status.value,
            },
        )
        return saved

    def retry_run(self, run_id: str, reason: str = "Retry requested") -> AgentRun:
        """Reset a FAILED AgentRun back to READY if retry limits allow."""
        run = self.get_run(run_id)
        if run.status != AgentRunStatus.FAILED:
            raise InvalidRunStateTransitionError(
                current_status=run.status.value,
                target_status=AgentRunStatus.READY.value,
                reason="Only FAILED runs can be retried.",
            )

        agent = self.agent_repo.get_by_id(run.agent_id)
        max_retries = agent.limits.max_retries if agent else 3

        if run.retry_count >= max_retries:
            raise AgentLimitExceededError(
                limit_name="max_retries",
                current_val=run.retry_count + 1,
                max_val=max_retries,
            )

        now = datetime.utcnow()
        updated_dict = run.model_dump()
        updated_dict["status"] = AgentRunStatus.READY
        updated_dict["retry_count"] = run.retry_count + 1
        updated_dict["failure"] = None
        updated_dict["updated_at"] = now

        reset_run = AgentRun(**updated_dict)
        saved = self.run_repo.save(reset_run)

        self.trace_service.record_event(
            event_type=AgentEventType.RUN_RESUMED,
            agent_id=saved.agent_id,
            run_id=saved.run_id,
            summary=f"AgentRun retried ({saved.retry_count}/{max_retries}): {reason}",
        )
        return saved

    def list_runs(
        self,
        agent_id: str | None = None,
        task_id: str | None = None,
        owner_id: str | None = None,
        status: AgentRunStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AgentRun], int]:
        """List AgentRuns with pagination."""
        return self.run_repo.list_runs(
            agent_id=agent_id,
            task_id=task_id,
            owner_id=owner_id,
            status=status,
            limit=limit,
            offset=offset,
        )
