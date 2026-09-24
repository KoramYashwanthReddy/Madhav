"""Pydantic API request/response schemas for Module 28."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from max.scheduler.domain.enums import (
    AutomationStatus,
    ConcurrencyPolicy,
    ExecutionStatus,
    MisfirePolicy,
    ScheduleStatus,
    ScheduleType,
    TriggerType,
)
from max.scheduler.domain.models import (
    AutomationDefinition,
    RecurrenceRule,
    RetryPolicy,
    Trigger,
)


class ScheduleCreateRequest(BaseModel):
    """Schema for creating a schedule."""

    schedule_type: ScheduleType = Field(default=ScheduleType.ONE_TIME)
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
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScheduleUpdateRequest(BaseModel):
    """Schema for updating a schedule."""

    cron_expression: str | None = None
    interval_seconds: float | None = None
    scheduled_at: datetime | None = None
    recurrence_rule: RecurrenceRule | None = None
    timezone: str | None = None
    misfire_policy: MisfirePolicy | None = None
    concurrency_policy: ConcurrencyPolicy | None = None
    metadata: dict[str, Any] | None = None


class ScheduleResponse(BaseModel):
    """Schema for schedule API response."""

    schedule_id: str
    schedule_type: ScheduleType
    status: ScheduleStatus
    owner_id: str
    automation_id: str | None = None
    cron_expression: str | None = None
    interval_seconds: float | None = None
    scheduled_at: datetime | None = None
    recurrence_rule: RecurrenceRule | None = None
    timezone: str
    misfire_policy: MisfirePolicy
    concurrency_policy: ConcurrencyPolicy
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None
    consecutive_failures: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class AutomationCreateRequest(BaseModel):
    """Schema for creating an automation."""

    name: str = Field(description="Automation display name")
    description: str = Field(default="")
    owner_id: str = Field(default="default_user")
    definition: AutomationDefinition = Field(default_factory=AutomationDefinition)
    trigger: Trigger | None = None
    dependencies: list[str] = Field(default_factory=list)
    concurrency_policy: ConcurrencyPolicy = Field(default=ConcurrencyPolicy.FORBID)
    misfire_policy: MisfirePolicy = Field(default=MisfirePolicy.SKIP)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AutomationUpdateRequest(BaseModel):
    """Schema for updating an automation."""

    name: str | None = None
    description: str | None = None
    definition: AutomationDefinition | None = None
    trigger: Trigger | None = None
    dependencies: list[str] | None = None
    concurrency_policy: ConcurrencyPolicy | None = None
    misfire_policy: MisfirePolicy | None = None
    metadata: dict[str, Any] | None = None


class AutomationResponse(BaseModel):
    """Schema for automation API response."""

    automation_id: str
    name: str
    description: str
    status: AutomationStatus
    owner_id: str
    definition: AutomationDefinition
    version: int
    trigger: Trigger | None = None
    dependencies: list[str]
    concurrency_policy: ConcurrencyPolicy
    misfire_policy: MisfirePolicy
    retry_policy: RetryPolicy
    metadata: dict[str, Any]


class ExecutionResponse(BaseModel):
    """Schema for execution history API response."""

    execution_id: str
    schedule_id: str | None = None
    automation_id: str
    automation_version: int
    owner_id: str
    trigger_type: TriggerType
    status: ExecutionStatus
    idempotency_key: str
    scheduled_at: datetime
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    steps_completed: list[str]
    steps_failed: list[str]
    permission_decisions: list[dict[str, Any]]
    result: dict[str, Any]
    error: str | None = None
    paused_step_id: str | None = None
    approval_request_id: str | None = None


class DryRunResponse(BaseModel):
    """Schema for dry run execution plan response."""

    automation_id: str
    version: int
    total_steps: int
    steps: list[dict[str, Any]]
