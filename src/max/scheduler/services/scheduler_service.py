"""Scheduler Service — Master orchestrator for schedules, misfire policies, locks, and triggers."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from max.scheduler.domain.enums import (
    ConcurrencyPolicy,
    ExecutionStatus,
    MisfirePolicy,
    ScheduleStatus,
    ScheduleType,
    TriggerType,
)
from max.scheduler.domain.exceptions import (
    ScheduleNotFoundError,
    ScheduleValidationError,
)
from max.scheduler.domain.models import (
    Execution,
    Schedule,
    ScheduleEvent,
    SchedulerAuditEvent,
    Trigger,
)
from max.scheduler.domain.state_machine import validate_schedule_transition
from max.scheduler.recurrence.engine import RecurrenceEngine
from max.scheduler.repositories.repositories import (
    BaseAuditRepository,
    BaseExecutionRepository,
    BaseScheduleRepository,
    BaseSchedulerLockRepository,
    BaseTriggerRepository,
)
from max.scheduler.services.automation_engine import AutomationEngineService
from max.scheduler.triggers.evaluator import MasterTriggerEvaluator

logger = logging.getLogger(__name__)


class SchedulerService:
    """Master Scheduler service managing schedules, triggers, misfires, concurrency, and execution loop."""

    def __init__(
        self,
        schedule_repo: BaseScheduleRepository,
        execution_repo: BaseExecutionRepository,
        trigger_repo: BaseTriggerRepository,
        lock_repo: BaseSchedulerLockRepository,
        audit_repo: BaseAuditRepository,
        automation_engine: AutomationEngineService,
        lock_timeout_seconds: float = 30.0,
        misfire_policy: MisfirePolicy = MisfirePolicy.SKIP,
    ) -> None:
        self.schedule_repo = schedule_repo
        self.execution_repo = execution_repo
        self.trigger_repo = trigger_repo
        self.lock_repo = lock_repo
        self.audit_repo = audit_repo
        self.automation_engine = automation_engine
        self.lock_timeout_seconds = lock_timeout_seconds
        self.default_misfire_policy = misfire_policy
        self.trigger_evaluator = MasterTriggerEvaluator()

        self._running = False
        self._paused = False

    def create_schedule(self, schedule: Schedule) -> Schedule:
        """Create and activate a new schedule."""
        self._validate_schedule(schedule)

        # Calculate initial next_run_at
        now = datetime.now(UTC)
        if schedule.next_run_at is None:
            schedule.next_run_at = RecurrenceEngine.get_next_run_time(schedule, from_time=now)
        schedule.status = ScheduleStatus.SCHEDULED

        self.schedule_repo.save(schedule)
        self.audit_repo.save(
            SchedulerAuditEvent(
                schedule_id=schedule.schedule_id,
                automation_id=schedule.automation_id,
                actor=schedule.owner_id,
                action="SCHEDULE_CREATED",
            )
        )
        return schedule

    def update_schedule(self, schedule: Schedule) -> Schedule:
        """Update existing schedule parameters."""
        existing = self.schedule_repo.get_by_id(schedule.schedule_id)
        if not existing:
            raise ScheduleNotFoundError(schedule.schedule_id)

        self._validate_schedule(schedule)
        now = datetime.now(UTC)
        schedule.next_run_at = RecurrenceEngine.get_next_run_time(schedule, from_time=now)
        self.schedule_repo.save(schedule)

        self.audit_repo.save(
            SchedulerAuditEvent(
                schedule_id=schedule.schedule_id,
                automation_id=schedule.automation_id,
                actor=schedule.owner_id,
                action="SCHEDULE_UPDATED",
            )
        )
        return schedule

    def pause_schedule(self, schedule_id: str) -> Schedule:
        """Pause an active schedule."""
        schedule = self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise ScheduleNotFoundError(schedule_id)

        validate_schedule_transition(schedule.status, ScheduleStatus.PAUSED)
        schedule.status = ScheduleStatus.PAUSED
        self.schedule_repo.save(schedule)

        self.audit_repo.save(
            SchedulerAuditEvent(
                schedule_id=schedule_id,
                actor=schedule.owner_id,
                action="SCHEDULE_PAUSED",
            )
        )
        return schedule

    def resume_schedule(self, schedule_id: str) -> Schedule:
        """Resume a paused schedule."""
        schedule = self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise ScheduleNotFoundError(schedule_id)

        validate_schedule_transition(schedule.status, ScheduleStatus.SCHEDULED)
        schedule.status = ScheduleStatus.SCHEDULED
        schedule.next_run_at = RecurrenceEngine.get_next_run_time(schedule)
        self.schedule_repo.save(schedule)

        self.audit_repo.save(
            SchedulerAuditEvent(
                schedule_id=schedule_id,
                actor=schedule.owner_id,
                action="SCHEDULE_RESUMED",
            )
        )
        return schedule

    def cancel_schedule(self, schedule_id: str) -> Schedule:
        """Cancel a schedule."""
        schedule = self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise ScheduleNotFoundError(schedule_id)

        validate_schedule_transition(schedule.status, ScheduleStatus.CANCELLED)
        schedule.status = ScheduleStatus.CANCELLED
        schedule.next_run_at = None
        self.schedule_repo.save(schedule)

        self.audit_repo.save(
            SchedulerAuditEvent(
                schedule_id=schedule_id,
                actor=schedule.owner_id,
                action="SCHEDULE_CANCELLED",
            )
        )
        return schedule

    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule record."""
        return self.schedule_repo.delete(schedule_id)

    def trigger_manually(
        self, automation_id: str, owner_id: str = "default_user", dry_run: bool = False
    ) -> Execution:
        """Manually trigger an automation execution passing all security controls."""
        trg = Trigger(trigger_type=TriggerType.MANUAL_TRIGGER)
        eval_res = self.trigger_evaluator.evaluate(trg)
        if not eval_res.triggered:
            raise ScheduleValidationError("Manual trigger evaluation failed.")

        return self.automation_engine.execute_automation(
            automation_id=automation_id,
            trigger_type=TriggerType.MANUAL_TRIGGER,
            dry_run=dry_run,
        )

    def get_next_run(self, schedule_id: str) -> datetime | None:
        """Retrieve next scheduled run timestamp."""
        schedule = self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise ScheduleNotFoundError(schedule_id)
        return schedule.next_run_at

    def execute_due(self, current_time: datetime | None = None) -> list[Execution]:
        """Core scheduler loop tick: identify, lock, evaluate misfires, and execute due schedules."""
        if self._paused:
            return []

        now = current_time or datetime.now(UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)

        due_schedules = self.schedule_repo.get_due_schedules(cutoff_time=now)
        executions: list[Execution] = []

        for schedule in due_schedules:
            if not schedule.automation_id:
                continue

            # Lock resource to prevent concurrent worker duplicate execution
            lock_acquired = self.lock_repo.acquire(
                resource_id=schedule.schedule_id,
                owner_id="scheduler_service",
                timeout_seconds=self.lock_timeout_seconds,
            )
            if not lock_acquired:
                logger.info("Could not acquire lock for schedule '%s'. Skipping.", schedule.schedule_id)
                continue

            try:
                # Handle misfires if schedule was offline/delayed
                misfire_handled = self._evaluate_misfire(schedule, now)
                if misfire_handled:
                    continue

                # Handle Concurrency Policy (FORBID, REPLACE, QUEUE, ALLOW)
                if schedule.concurrency_policy == ConcurrencyPolicy.FORBID:
                    active = self.execution_repo.count_active_executions(
                        automation_id=schedule.automation_id
                    )
                    if active > 0:
                        logger.warning("FORBID concurrency policy blocked schedule '%s'.", schedule.schedule_id)
                        # Advance next run
                        schedule.next_run_at = RecurrenceEngine.get_next_run_time(schedule, from_time=now)
                        self.schedule_repo.save(schedule)
                        continue

                # Execute Automation
                schedule.status = ScheduleStatus.RUNNING
                self.schedule_repo.save(schedule)

                exc = self.automation_engine.execute_automation(
                    automation_id=schedule.automation_id,
                    schedule=schedule,
                    trigger_type=TriggerType.TIME_TRIGGER,
                )
                executions.append(exc)

                # Update schedule last_run_at and next_run_at
                schedule.last_run_at = now
                schedule.next_run_at = RecurrenceEngine.get_next_run_time(schedule, from_time=now)

                if exc.status == ExecutionStatus.COMPLETED:
                    schedule.consecutive_failures = 0
                    if schedule.schedule_type == ScheduleType.ONE_TIME or schedule.next_run_at is None:
                        schedule.status = ScheduleStatus.COMPLETED
                    else:
                        schedule.status = ScheduleStatus.SCHEDULED
                elif exc.status == ExecutionStatus.FAILED:
                    schedule.consecutive_failures += 1
                    schedule.status = ScheduleStatus.SCHEDULED

                self.schedule_repo.save(schedule)

            finally:
                self.lock_repo.release(resource_id=schedule.schedule_id, owner_id="scheduler_service")

        return executions

    def _evaluate_misfire(self, schedule: Schedule, now: datetime) -> bool:
        """Evaluate misfire policy if schedule missed execution by > 60s. Returns True if skipped."""
        if not schedule.next_run_at:
            return False

        next_run = schedule.next_run_at
        if next_run.tzinfo is None:
            next_run = next_run.replace(tzinfo=UTC)

        misfire_threshold_seconds = 60.0
        time_diff = (now - next_run).total_seconds()

        if time_diff > misfire_threshold_seconds:
            policy = schedule.misfire_policy or self.default_misfire_policy
            logger.warning(
                "Schedule '%s' misfired by %.1f seconds. Policy: %s",
                schedule.schedule_id,
                time_diff,
                policy.value,
            )

            if policy == MisfirePolicy.SKIP:
                schedule.next_run_at = RecurrenceEngine.get_next_run_time(schedule, from_time=now)
                self.schedule_repo.save(schedule)
                self.audit_repo.save(
                    SchedulerAuditEvent(
                        schedule_id=schedule.schedule_id,
                        action="EXECUTION_SKIPPED",
                        metadata={"reason": "misfire_skip"},
                    )
                )
                return True

        return False

    def process_event(self, event: ScheduleEvent) -> list[Execution]:
        """Process external or system event and trigger matching automations."""
        automations = self.automation_engine.automation_repo.list(limit=1000)
        executions: list[Execution] = []

        for aut in automations:
            if aut.trigger and aut.trigger.trigger_type == TriggerType.EVENT_TRIGGER:
                res = self.trigger_evaluator.evaluate(aut.trigger, event=event)
                if res.triggered:
                    exc = self.automation_engine.execute_automation(
                        automation_id=aut.automation_id,
                        trigger_type=TriggerType.EVENT_TRIGGER,
                        event_payload=event.payload,
                    )
                    executions.append(exc)

        return executions

    def _validate_schedule(self, schedule: Schedule) -> None:
        """Validate schedule configuration."""
        if schedule.schedule_type == ScheduleType.CRON and not schedule.cron_expression:
            raise ScheduleValidationError("CRON schedule type requires cron_expression.")
        if schedule.schedule_type == ScheduleType.INTERVAL and (
            not schedule.interval_seconds or schedule.interval_seconds <= 0
        ):
            raise ScheduleValidationError("INTERVAL schedule type requires positive interval_seconds.")

    def start(self) -> None:
        """Start scheduler processing loop."""
        self._running = True
        self._paused = False

    def stop(self) -> None:
        """Gracefully stop scheduler loop."""
        self._running = False

    def pause(self) -> None:
        """Pause processing loop."""
        self._paused = True

    def resume(self) -> None:
        """Resume processing loop."""
        self._paused = False

    def health(self) -> dict[str, Any]:
        """Return health status."""
        return {"status": "HEALTHY", "running": self._running, "paused": self._paused}
