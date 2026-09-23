"""API response models for Module 12 Task Engine endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from madhav.tasks.domain.enums import (
    DependencyType,
    TaskGroupStatus,
    TaskPriority,
    TaskReadinessStatus,
    TaskSource,
    TaskStatus,
    TaskType,
)
from madhav.tasks.domain.history import TaskHistoryEntry
from madhav.tasks.domain.references import TaskReference
from madhav.tasks.domain.schedule import TaskSchedule
from madhav.tasks.domain.task import TaskFailure, TaskResult


class TaskResponse(BaseModel):
    """Full task record response object."""

    id: str
    owner_id: str
    title: str
    description: str
    type: TaskType
    status: TaskStatus
    priority: TaskPriority
    progress: int
    source: TaskSource
    plan_id: str | None = None
    plan_version: int | None = None
    plan_step_id: str | None = None
    reasoning_id: str | None = None
    conversation_id: str | None = None
    parent_task_id: str | None = None
    group_id: str | None = None
    schedule: TaskSchedule | None = None
    due_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    result: TaskResult | None = None
    failure: TaskFailure | None = None
    retry_count: int
    max_retries: int
    last_retry_at: datetime | None = None
    retryable: bool
    references: list[TaskReference] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskListResponse(BaseModel):
    """Paginated response containing list of tasks and pagination metadata."""

    items: list[TaskResponse]
    total: int
    limit: int
    offset: int


class TaskDependencyResponse(BaseModel):
    """Task dependency edge response model."""

    dependency_id: str
    source_task_id: str
    target_task_id: str
    dependency_type: DependencyType
    created_at: datetime


class TaskDependencyListResponse(BaseModel):
    """List response for task dependencies."""

    incoming_dependencies: list[TaskDependencyResponse]
    outgoing_dependents: list[TaskDependencyResponse]


class TaskGroupResponse(BaseModel):
    """Task group record response model."""

    group_id: str
    owner_id: str
    name: str
    description: str
    status: TaskGroupStatus
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskGroupListResponse(BaseModel):
    """Paginated task group listing response."""

    items: list[TaskGroupResponse]
    total: int
    limit: int
    offset: int


class TaskGroupSummaryResponse(BaseModel):
    """Summary metrics response model for a task group."""

    group_id: str
    name: str
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    blocked_tasks: int
    in_progress_tasks: int
    overall_progress: float


class TaskHistoryListResponse(BaseModel):
    """Paginated list response for task audit trail entries."""

    items: list[TaskHistoryEntry]
    total: int
    limit: int
    offset: int


class TaskReadinessResponse(BaseModel):
    """Readiness status evaluation response model."""

    task_id: str
    readiness_status: TaskReadinessStatus
    current_status: TaskStatus


class PlanConversionResponse(BaseModel):
    """Response returned upon converting a plan into tasks."""

    plan_id: str
    plan_version: int
    generated_tasks_count: int
    generated_dependencies_count: int
    tasks: list[TaskResponse]
