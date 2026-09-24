"""Domain entities for Module 28 — Scheduler & Automation Engine."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from max.scheduler.domain.enums import (
    AutomationStatus,
    BackoffStrategy,
    ConcurrencyPolicy,
    ConditionOperator,
    ExecutionStatus,
    MisfirePolicy,
    ScheduleStatus,
    ScheduleType,
    StepType,
    TriggerStatus,
    TriggerType,
)


class RecurrenceRule(BaseModel):
    """Configuration for recurring schedule rules."""

    frequency: str = Field(description="SECOND, MINUTE, HOUR, DAILY, WEEKLY, MONTHLY, YEARLY")
    interval: int = Field(default=1, ge=1, description="Interval spacing")
    by_day: list[str] | None = Field(default=None, description="e.g. ['MON', 'TUE', 'WED', 'THU', 'FRI']")
    by_month_day: list[int] | None = Field(default=None, description="Day numbers 1..31")
    by_month: list[int] | None = Field(default=None, description="Month numbers 1..12")
    by_hour: list[int] | None = Field(default=None, description="Hours 0..23")
    by_minute: list[int] | None = Field(default=None, description="Minutes 0..59")
    by_second: list[int] | None = Field(default=None, description="Seconds 0..59")
    start_at: datetime | None = None
    end_at: datetime | None = None
    count: int | None = Field(default=None, ge=1, description="Max occurrences")
    timezone: str = Field(default="UTC", description="IANA timezone name")


class ScheduleWindow(BaseModel):
    """Allowed time window for execution."""

    start_time: str = Field(description="Start time HH:MM format")
    end_time: str = Field(description="End time HH:MM format")
    timezone: str = Field(default="UTC", description="IANA timezone name")


class RetryPolicy(BaseModel):
    """Retry policy for failed executions."""

    max_attempts: int = Field(default=3, ge=0, description="Max execution attempts")
    initial_delay_seconds: float = Field(default=5.0, ge=0.0, description="Initial retry delay")
    max_delay_seconds: float = Field(default=300.0, ge=0.0, description="Max backoff ceiling")
    backoff_strategy: BackoffStrategy = Field(
        default=BackoffStrategy.EXPONENTIAL_BACKOFF, description="Backoff algorithm"
    )


class AutomationCondition(BaseModel):
    """Structured condition evaluation entity (no eval/exec)."""

    condition_type: str = Field(default="COMPARISON", description="Category of condition")
    operator: ConditionOperator = Field(default=ConditionOperator.EQUALS)
    expected_value: Any = Field(default=True)
    actual_value_path: str | None = Field(
        default=None, description="JSON path or context key to extract actual value"
    )


class TriggerDefinition(BaseModel):
    """Underlying definition details for a trigger."""

    cron_expression: str | None = None
    interval_seconds: float | None = None
    event_type: str | None = None
    event_source: str | None = None
    condition: AutomationCondition | None = None


class Trigger(BaseModel):
    """Trigger entity governing when automations run."""

    trigger_id: str = Field(default_factory=lambda: f"trg_{uuid4().hex[:12]}")
    trigger_type: TriggerType = Field(default=TriggerType.TIME_TRIGGER)
    status: TriggerStatus = Field(default=TriggerStatus.ACTIVE)
    definition: TriggerDefinition = Field(default_factory=TriggerDefinition)
    source: str = Field(default="system")
    condition: AutomationCondition | None = None


class AutomationStep(BaseModel):
    """Individual structured step within an automation workflow."""

    step_id: str = Field(default_factory=lambda: f"step_{uuid4().hex[:8]}")
    step_type: StepType = Field(default=StepType.CREATE_TASK)
    order: int = Field(default=0)
    configuration: dict[str, Any] = Field(default_factory=dict)
    condition: AutomationCondition | None = None
    dependencies: list[str] = Field(default_factory=list)
    timeout_seconds: float | None = None
    retry_policy: RetryPolicy | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AutomationDefinition(BaseModel):
    """Structured workflow definition containing steps and targets."""

    steps: list[AutomationStep] = Field(default_factory=list)
    target_task_name: str | None = None
    target_agent_id: str | None = None
    target_tool_id: str | None = None


class Automation(BaseModel):
    """Automation entity representing a complete workflow pipeline."""

    automation_id: str = Field(default_factory=lambda: f"aut_{uuid4().hex[:12]}")
    name: str = Field(description="Automation display name")
    description: str = Field(default="")
    status: AutomationStatus = Field(default=AutomationStatus.SCHEDULED)
    owner_id: str = Field(default="default_user")
    definition: AutomationDefinition = Field(default_factory=AutomationDefinition)
    version: int = Field(default=1, ge=1)
    trigger: Trigger | None = None
    dependencies: list[str] = Field(
        default_factory=list, description="IDs of other automations this automation depends on"
    )
    concurrency_policy: ConcurrencyPolicy = Field(default=ConcurrencyPolicy.FORBID)
    misfire_policy: MisfirePolicy = Field(default=MisfirePolicy.SKIP)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Schedule(BaseModel):
    """Schedule entity determining WHEN an automation or task triggers."""

    schedule_id: str = Field(default_factory=lambda: f"sch_{uuid4().hex[:12]}")
    schedule_type: ScheduleType = Field(default=ScheduleType.ONE_TIME)
    status: ScheduleStatus = Field(default=ScheduleStatus.SCHEDULED)
    owner_id: str = Field(default="default_user")
    automation_id: str | None = None
    cron_expression: str | None = None
    interval_seconds: float | None = None
    scheduled_at: datetime | None = None
    recurrence_rule: RecurrenceRule | None = None
    timezone: str = Field(default="UTC")
    misfire_policy: MisfirePolicy = Field(default=MisfirePolicy.SKIP)
    concurrency_policy: ConcurrencyPolicy = Field(default=ConcurrencyPolicy.FORBID)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None
    consecutive_failures: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionAttempt(BaseModel):
    """Single attempt record within an execution."""

    attempt_id: str = Field(default_factory=lambda: f"att_{uuid4().hex[:8]}")
    attempt_number: int = Field(default=1, ge=1)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    status: ExecutionStatus = Field(default=ExecutionStatus.RUNNING)
    error: str | None = None
    retry_at: datetime | None = None


class Execution(BaseModel):
    """Execution state entity tracking a single run of an automation."""

    execution_id: str = Field(default_factory=lambda: f"exc_{uuid4().hex[:12]}")
    schedule_id: str | None = None
    automation_id: str = Field(description="Target automation ID")
    automation_version: int = Field(default=1)
    owner_id: str = Field(default="default_user")
    trigger_type: TriggerType = Field(default=TriggerType.TIME_TRIGGER)
    status: ExecutionStatus = Field(default=ExecutionStatus.RUNNING)
    idempotency_key: str = Field(default="")
    scheduled_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    attempts: list[ExecutionAttempt] = Field(default_factory=list)
    steps_completed: list[str] = Field(default_factory=list)
    steps_failed: list[str] = Field(default_factory=list)
    permission_decisions: list[dict[str, Any]] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    paused_step_id: str | None = None
    approval_request_id: str | None = None


class ScheduleEvent(BaseModel):
    """External or system event model triggering automations."""

    event_id: str = Field(default_factory=lambda: f"evt_{uuid4().hex[:12]}")
    event_type: str = Field(description="e.g. github.pull_request.created")
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source: str = Field(default="system")
    payload: dict[str, Any] = Field(default_factory=dict)


class SchedulerLock(BaseModel):
    """Concurrency control distributed lock entity."""

    lock_id: str = Field(default_factory=lambda: f"lck_{uuid4().hex[:12]}")
    resource_id: str = Field(description="Target resource or schedule ID being locked")
    owner_id: str = Field(default="scheduler_worker")
    acquired_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = Field(description="Lock expiration timestamp")


class SchedulerAuditEvent(BaseModel):
    """Audit log entry for scheduler & automation operations."""

    event_id: str = Field(default_factory=lambda: f"aud_{uuid4().hex[:12]}")
    schedule_id: str | None = None
    automation_id: str | None = None
    execution_id: str | None = None
    actor: str = Field(default="system")
    action: str = Field(description="Audited action name")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)
