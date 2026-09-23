"""Task entity and outcome models for Module 12 Task Engine."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from max.tasks.domain.enums import TaskPriority, TaskSource, TaskStatus, TaskType
from max.tasks.domain.references import TaskReference
from max.tasks.domain.schedule import TaskSchedule


class TaskResult(BaseModel):
    """Structured outcome data produced upon task completion (Future-compatible representation)."""

    model_config = ConfigDict(frozen=True)

    status: TaskStatus = Field(default=TaskStatus.COMPLETED, description="Completion status")
    summary: str = Field(default="Task completed", description="Human-readable execution summary")
    output_reference: str | None = Field(
        default=None, description="Pointer to generated output artifact"
    )
    completed_at: datetime = Field(
        default_factory=datetime.utcnow, description="Completion timestamp"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary output metadata")


class TaskFailure(BaseModel):
    """Structured failure diagnosis for a failed task."""

    model_config = ConfigDict(frozen=True)

    error_code: str = Field(default="TASK_FAILED", description="Error taxonomy code")
    summary: str = Field(description="Descriptive failure message")
    retryable: bool = Field(default=True, description="Whether failure condition permits retry")
    occurred_at: datetime = Field(
        default_factory=datetime.utcnow, description="Failure occurrence timestamp"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Error context metadata")


class Task(BaseModel):
    """Core domain entity representing one unit of work."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(
        default_factory=lambda: f"task_{uuid4().hex[:12]}", description="Unique task identifier"
    )
    owner_id: str = Field(description="User ID owning the task")
    title: str = Field(description="Short descriptive title of the task")
    description: str = Field(default="", description="Detailed work description")
    type: TaskType = Field(default=TaskType.GENERAL, description="Category type of work")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current lifecycle state")
    priority: TaskPriority = Field(
        default=TaskPriority.NORMAL, description="Controlled priority level"
    )
    progress: int = Field(default=0, ge=0, le=100, description="Completion percentage (0 to 100)")
    source: TaskSource = Field(default=TaskSource.MANUAL, description="Origin category")

    plan_id: str | None = Field(
        default=None, description="Linked Module 11 plan ID if derived from plan"
    )
    plan_version: int | None = Field(default=None, description="Plan version number")
    plan_step_id: str | None = Field(default=None, description="Linked plan step ID")
    reasoning_id: str | None = Field(default=None, description="Linked reasoning request ID")
    conversation_id: str | None = Field(default=None, description="Linked conversation ID")
    parent_task_id: str | None = Field(
        default=None, description="Parent task ID for hierarchical subtasks"
    )
    group_id: str | None = Field(default=None, description="Assigned task group ID")

    schedule: TaskSchedule | None = Field(default=None, description="Schedule and timing metadata")
    due_at: datetime | None = Field(default=None, description="Explicit deadline cutoff")

    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    started_at: datetime | None = Field(
        default=None, description="Timestamp when task transitioned to IN_PROGRESS"
    )
    completed_at: datetime | None = Field(
        default=None, description="Timestamp when task reached COMPLETED"
    )
    cancelled_at: datetime | None = Field(
        default=None, description="Timestamp when task was CANCELLED"
    )

    result: TaskResult | None = Field(default=None, description="Outcome result if task completed")
    failure: TaskFailure | None = Field(
        default=None, description="Failure diagnostic if task failed"
    )

    retry_count: int = Field(default=0, ge=0, description="Current number of retries attempted")
    max_retries: int = Field(default=3, ge=0, description="Maximum allowed retries")
    last_retry_at: datetime | None = Field(
        default=None, description="Timestamp of last retry reset"
    )
    retryable: bool = Field(
        default=True, description="Flag indicating if task can be retried upon failure"
    )

    references: list[TaskReference] = Field(default_factory=list, description="Artifact references")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary task metadata")


class TaskSummary(BaseModel):
    """Compact representation of a task for listings and summaries."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Task ID")
    title: str = Field(description="Task title")
    status: TaskStatus = Field(description="Current task status")
    priority: TaskPriority = Field(description="Task priority")
    progress: int = Field(description="Progress percentage")
    owner_id: str = Field(description="Owner user ID")
    group_id: str | None = Field(default=None, description="Task group ID")
    plan_id: str | None = Field(default=None, description="Plan ID")
    due_at: datetime | None = Field(default=None, description="Due date")
    dependency_status: str = Field(default="UNKNOWN", description="Calculated dependency status")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Update timestamp")
