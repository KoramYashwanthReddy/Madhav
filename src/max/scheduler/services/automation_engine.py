"""Automation Engine for orchestrating structured workflows, steps, and module integrations."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from max.scheduler.domain.enums import (
    AutomationStatus,
    ExecutionStatus,
    StepType,
    TriggerType,
)
from max.scheduler.domain.exceptions import (
    AutomationNotFoundError,
    AutomationValidationError,
    CircularDependencyError,
    RateLimitExceededError,
)
from max.scheduler.domain.models import (
    Automation,
    AutomationStep,
    Execution,
    ExecutionAttempt,
    Schedule,
    SchedulerAuditEvent,
)
from max.scheduler.domain.state_machine import validate_automation_transition
from max.scheduler.integrations.adapters import (
    AgentEngineAdapter,
    NotificationAdapter,
    PermissionSecurityAdapter,
    TaskEngineAdapter,
    ToolRegistryAdapter,
)
from max.scheduler.repositories.repositories import (
    BaseAuditRepository,
    BaseAutomationRepository,
    BaseExecutionRepository,
)
from max.scheduler.triggers.evaluator import evaluate_condition

logger = logging.getLogger(__name__)


def detect_circular_dependencies(
    automations_map: dict[str, Automation], start_id: str, visited: set[str] | None = None, stack: set[str] | None = None
) -> None:
    """Detect circular dependencies in automation graph using DFS."""
    v = visited if visited is not None else set()
    s = stack if stack is not None else set()

    v.add(start_id)
    s.add(start_id)

    aut = automations_map.get(start_id)
    if aut:
        for dep_id in aut.dependencies:
            if dep_id not in v:
                detect_circular_dependencies(automations_map, dep_id, v, s)
            elif dep_id in s:
                raise CircularDependencyError(
                    f"Circular dependency detected involving automation '{start_id}' and '{dep_id}'."
                )

    s.remove(start_id)


class AutomationEngineService:
    """Orchestrates automation workflows, steps, versions, and security controls."""

    def __init__(
        self,
        automation_repo: BaseAutomationRepository,
        execution_repo: BaseExecutionRepository,
        audit_repo: BaseAuditRepository,
        task_adapter: TaskEngineAdapter | None = None,
        agent_adapter: AgentEngineAdapter | None = None,
        tool_adapter: ToolRegistryAdapter | None = None,
        security_adapter: PermissionSecurityAdapter | None = None,
        notification_adapter: NotificationAdapter | None = None,
        circuit_breaker_threshold: int = 10,
        max_executions_per_minute: int = 60,
    ) -> None:
        self.automation_repo = automation_repo
        self.execution_repo = execution_repo
        self.audit_repo = audit_repo
        self.task_adapter = task_adapter or TaskEngineAdapter()
        self.agent_adapter = agent_adapter or AgentEngineAdapter()
        self.tool_adapter = tool_adapter or ToolRegistryAdapter()
        self.security_adapter = security_adapter or PermissionSecurityAdapter()
        self.notification_adapter = notification_adapter or NotificationAdapter()
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.max_executions_per_minute = max_executions_per_minute

    def create_automation(self, automation: Automation) -> Automation:
        """Create and persist new Automation definition."""
        self._validate_automation_definition(automation)
        self.automation_repo.save(automation)
        self.audit_repo.save(
            SchedulerAuditEvent(
                automation_id=automation.automation_id,
                actor=automation.owner_id,
                action="AUTOMATION_CREATED",
            )
        )
        return automation

    def update_automation(self, automation: Automation) -> Automation:
        """Update automation definition and increment version for active executions."""
        existing = self.automation_repo.get_by_id(automation.automation_id)
        if not existing:
            raise AutomationNotFoundError(automation.automation_id)

        self._validate_automation_definition(automation)
        # Increment version on edit
        automation.version = existing.version + 1
        self.automation_repo.save(automation)

        self.audit_repo.save(
            SchedulerAuditEvent(
                automation_id=automation.automation_id,
                actor=automation.owner_id,
                action="AUTOMATION_UPDATED",
                metadata={"new_version": automation.version},
            )
        )
        return automation

    def _validate_automation_definition(self, automation: Automation) -> None:
        """Validate automation definition and check circular dependencies."""
        if not automation.name.strip():
            raise AutomationValidationError("Automation name cannot be empty.")

        # Check circular dependencies across saved automations
        all_automations = {a.automation_id: a for a in self.automation_repo.list(limit=1000)}
        all_automations[automation.automation_id] = automation
        try:
            detect_circular_dependencies(all_automations, automation.automation_id)
        except CircularDependencyError:
            raise

    def execute_automation(
        self,
        automation_id: str,
        schedule: Schedule | None = None,
        trigger_type: TriggerType = TriggerType.TIME_TRIGGER,
        dry_run: bool = False,
        event_payload: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> Execution:
        """Execute or dry-run an automation workflow step-by-step."""
        automation = self.automation_repo.get_by_id(automation_id)
        if not automation:
            raise AutomationNotFoundError(automation_id)

        if automation.status in (AutomationStatus.DISABLED, AutomationStatus.CANCELLED):
            raise AutomationValidationError(
                f"Cannot execute automation '{automation_id}' in state '{automation.status}'."
            )

        now = datetime.now(UTC)
        occurrence_str = (
            schedule.next_run_at.isoformat()
            if schedule and schedule.next_run_at
            else now.isoformat()
        )
        idempotency_key = f"{schedule.schedule_id if schedule else automation_id}:{occurrence_str}:{automation.version}"

        # Idempotency check
        existing_exc = self.execution_repo.get_by_idempotency_key(idempotency_key)
        if existing_exc and not dry_run:
            logger.info("Duplicate execution detected for key '%s'. Returning existing record.", idempotency_key)
            return existing_exc

        # Rate limit check
        recent_count = self.execution_repo.count_active_executions(
            automation_id=automation_id, owner_id=automation.owner_id
        )
        if recent_count >= self.max_executions_per_minute and not dry_run:
            raise RateLimitExceededError(
                f"Rate limit exceeded for automation '{automation_id}'. Active: {recent_count}."
            )

        execution = Execution(
            schedule_id=schedule.schedule_id if schedule else None,
            automation_id=automation_id,
            automation_version=automation.version,
            owner_id=automation.owner_id,
            trigger_type=trigger_type,
            status=ExecutionStatus.RUNNING,
            idempotency_key=idempotency_key,
            scheduled_at=schedule.next_run_at if schedule and schedule.next_run_at else now,
            started_at=now,
            attempts=[ExecutionAttempt(attempt_number=1, started_at=now)],
        )

        if dry_run:
            execution.result["dry_run"] = True
            execution.result["plan"] = self._build_dry_run_plan(automation, context)
            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.now(UTC)
            return execution

        self.execution_repo.save(execution)
        self.notification_adapter.send_scheduler_notification(
            owner_id=automation.owner_id,
            title=f"Automation Started: {automation.name}",
            body=f"Execution '{execution.execution_id}' started for automation '{automation.name}'.",
            event_type="AUTOMATION_STARTED",
            metadata={"execution_id": execution.execution_id, "automation_id": automation_id},
        )

        # Check dependencies
        for dep_id in automation.dependencies:
            dep_execs = self.execution_repo.list(automation_id=dep_id, limit=1)
            if not dep_execs or dep_execs[0].status != ExecutionStatus.COMPLETED:
                execution.status = ExecutionStatus.FAILED
                execution.error = f"Dependency automation '{dep_id}' has not succeeded."
                execution.completed_at = datetime.now(UTC)
                self.execution_repo.save(execution)
                return execution

        # Execute steps
        eval_ctx = context.copy() if context else {}
        if event_payload:
            eval_ctx["event_payload"] = event_payload

        try:
            for step in automation.definition.steps:
                step_success, is_paused, pause_reason = self._execute_step(
                    automation=automation, step=step, execution=execution, context=eval_ctx
                )
                if is_paused:
                    execution.status = ExecutionStatus.PAUSED
                    execution.paused_step_id = step.step_id
                    execution.approval_request_id = pause_reason
                    self.execution_repo.save(execution)

                    self.notification_adapter.send_scheduler_notification(
                        owner_id=automation.owner_id,
                        title=f"Automation Paused (Approval Required): {automation.name}",
                        body=f"Execution paused at step '{step.step_id}'. Request ID: {pause_reason}",
                        event_type="APPROVAL_REQUIRED",
                        metadata={"execution_id": execution.execution_id, "approval_request_id": pause_reason},
                    )
                    return execution

                if not step_success:
                    execution.status = ExecutionStatus.FAILED
                    execution.steps_failed.append(step.step_id)
                    execution.completed_at = datetime.now(UTC)
                    self._handle_execution_failure(automation, execution)
                    return execution

                execution.steps_completed.append(step.step_id)

            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.now(UTC)
            if execution.started_at:
                execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
            self.execution_repo.save(execution)

            self.notification_adapter.send_scheduler_notification(
                owner_id=automation.owner_id,
                title=f"Automation Completed: {automation.name}",
                body=f"Execution '{execution.execution_id}' completed successfully.",
                event_type="AUTOMATION_COMPLETED",
                metadata={"execution_id": execution.execution_id},
            )

        except Exception as exc:
            logger.exception("Unexpected error executing automation '%s': %s", automation_id, exc)
            execution.status = ExecutionStatus.FAILED
            execution.error = str(exc)
            execution.completed_at = datetime.now(UTC)
            self._handle_execution_failure(automation, execution)

        return execution

    def _execute_step(
        self,
        automation: Automation,
        step: AutomationStep,
        execution: Execution,
        context: dict[str, Any],
    ) -> tuple[bool, bool, str | None]:
        """Execute a single step. Returns (success, is_paused, pause_reason_or_req_id)."""
        # 1. Evaluate step condition if present
        if step.condition and not evaluate_condition(step.condition, context):
            logger.info("Step '%s' condition evaluated to False. Skipping step.", step.step_id)
            return True, False, None

        # 2. Permission Security check (Module 15 is authoritative!)
        action_name = f"STEP_{step.step_type.value}"
        is_allowed, dec_status, detail = self.security_adapter.check_permission(
            subject_id=automation.owner_id,
            resource_id=f"automation:{automation.automation_id}:step:{step.step_id}",
            action_name=action_name,
            metadata={"step_type": step.step_type.value},
        )

        execution.permission_decisions.append(
            {"step_id": step.step_id, "status": dec_status, "detail": detail}
        )

        if dec_status == "REQUIRE_APPROVAL":
            return False, True, detail  # detail is approval_request_id

        if not is_allowed:
            execution.error = f"Permission denied for step '{step.step_id}': {detail}"
            return False, False, None

        # 3. Dispatch step logic based on step_type
        if step.step_type == StepType.CREATE_TASK:
            task_name = step.configuration.get("task_name", f"Task for {automation.name}")
            task = self.task_adapter.create_task_for_automation(
                name=task_name,
                description=step.configuration.get("description", ""),
                owner_id=automation.owner_id,
                metadata={"automation_id": automation.automation_id, "execution_id": execution.execution_id},
            )
            context["created_task_id"] = task.id
            execution.result[f"step_{step.step_id}_task_id"] = task.id

        elif step.step_type == StepType.ASSIGN_AGENT:
            task_id = context.get("created_task_id")
            if task_id:
                retrieved_task = self.task_adapter.get_task(task_id)
                if retrieved_task is not None:
                    self.agent_adapter.assign_and_execute_task(
                        task=retrieved_task, agent_id=step.configuration.get("agent_id")
                    )

        elif step.step_type == StepType.EXECUTE_TOOL:
            tool_id = step.configuration.get("tool_id", "")
            args = step.configuration.get("arguments", {})
            res = self.tool_adapter.invoke_tool(tool_id=tool_id, arguments=args, owner_id=automation.owner_id)
            execution.result[f"step_{step.step_id}_tool_output"] = res
            if res.get("status") == "FAILED":
                execution.error = f"Tool '{tool_id}' execution failed: {res.get('error')}"
                return False, False, None

        elif step.step_type == StepType.WAIT:
            # Represent delay as execution state rather than blocking thread
            delay_sec = float(step.configuration.get("seconds", 0))
            context["wait_until"] = (datetime.now(UTC)).timestamp() + delay_sec
            execution.result[f"step_{step.step_id}_wait_seconds"] = delay_sec

        elif step.step_type == StepType.SEND_NOTIFICATION:
            title = step.configuration.get("title", f"Notification: {automation.name}")
            body = step.configuration.get("body", "Automation step executed.")
            self.notification_adapter.send_scheduler_notification(
                owner_id=automation.owner_id,
                title=title,
                body=body,
                metadata={"execution_id": execution.execution_id},
            )

        return True, False, None

    def _handle_execution_failure(self, automation: Automation, execution: Execution) -> None:
        """Handle execution failure, circuit breaker, and audit logging."""
        self.execution_repo.save(execution)
        self.audit_repo.save(
            SchedulerAuditEvent(
                automation_id=automation.automation_id,
                execution_id=execution.execution_id,
                actor=automation.owner_id,
                action="EXECUTION_FAILED",
                metadata={"error": execution.error},
            )
        )

        # Circuit breaker evaluation
        recent_execs = self.execution_repo.list(automation_id=automation.automation_id, limit=self.circuit_breaker_threshold)
        consecutive_fails = 0
        for exc in recent_execs:
            if exc.status == ExecutionStatus.FAILED:
                consecutive_fails += 1
            else:
                break

        if consecutive_fails >= self.circuit_breaker_threshold:
            logger.warning(
                "Circuit breaker tripped for automation '%s' (%d consecutive failures). Disabling automation.",
                automation.automation_id,
                consecutive_fails,
            )
            validate_automation_transition(automation.status, AutomationStatus.DISABLED)
            automation.status = AutomationStatus.DISABLED
            self.automation_repo.save(automation)

            self.notification_adapter.send_scheduler_notification(
                owner_id=automation.owner_id,
                title=f"Automation Disabled (Circuit Breaker): {automation.name}",
                body=f"Automation '{automation.name}' was automatically disabled after {consecutive_fails} consecutive failures.",
                event_type="CIRCUIT_BREAKER_TRIPPED",
                metadata={"automation_id": automation.automation_id},
            )

    def _build_dry_run_plan(
        self, automation: Automation, context: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Build execution dry run preview plan without side effects."""
        plan_steps = []
        for step in automation.definition.steps:
            plan_steps.append(
                {
                    "step_id": step.step_id,
                    "step_type": step.step_type.value,
                    "order": step.order,
                    "configuration": step.configuration,
                    "condition_check": "EVALUATED_OK" if step.condition is None else "CONDITIONAL",
                    "estimated_permission": "ALLOWED",
                }
            )
        return {
            "automation_id": automation.automation_id,
            "version": automation.version,
            "total_steps": len(plan_steps),
            "steps": plan_steps,
        }
