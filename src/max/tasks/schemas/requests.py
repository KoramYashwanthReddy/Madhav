"""API request models for Module 12 Task Engine endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from max.tasks.domain.enums import (
    DependencyType,
    TaskGroupStatus,
    TaskPriority,
    TaskSource,
    TaskType,
)
from max.tasks.domain.references import TaskReference
from max.tasks.domain.schedule import TaskSchedule


class CreateTaskRequest(BaseModel):
    """Payload model for creating a new Task."""

    owner_id: str = Field(description="User ID owning the task")
    title: str = Field(description="Short title for the task")
    description: str = Field(default="", description="Detailed work description")
    type: TaskType = Field(default=TaskType.GENERAL, description="Task category type")
    priority: TaskPriority = Field(default=TaskPriority.NORMAL, description="Task priority level")
    source: TaskSource = Field(default=TaskSource.MANUAL, description="Origin category")

    plan_id: str | None = Field(default=None, description="Linked plan ID")
    plan_version: int | None = Field(default=None, description="Linked plan version")
    plan_step_id: str | None = Field(default=None, description="Linked step ID")
    reasoning_id: str | None = Field(default=None, description="Linked reasoning request ID")
    conversation_id: str | None = Field(default=None, description="Linked conversation ID")
    parent_task_id: str | None = Field(default=None, description="Parent task ID")
    group_id: str | None = Field(default=None, description="Task group ID")

    schedule: TaskSchedule | None = Field(default=None, description="Schedule specification")
    due_at: datetime | None = Field(default=None, description="Explicit deadline cutoff")
    references: list[TaskReference] = Field(default_factory=list, description="Artifact references")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary task metadata")
    max_retries: int | None = Field(default=None, description="Maximum retry attempts allowed")


class UpdateTaskRequest(BaseModel):
    """Payload model for updating task properties."""

    title: str | None = Field(default=None, description="Updated title")
    description: str | None = Field(default=None, description="Updated description")
    priority: TaskPriority | None = Field(default=None, description="Updated priority")
    type: TaskType | None = Field(default=None, description="Updated type")
    due_at: datetime | None = Field(default=None, description="Updated due date")
    group_id: str | None = Field(default=None, description="Updated group assignment")
    parent_task_id: str | None = Field(default=None, description="Updated parent task ID")
    metadata: dict[str, Any] | None = Field(default=None, description="Metadata updates to merge")


class UpdateTaskProgressRequest(BaseModel):
    """Payload model for updating task progress percentage."""

    progress: int = Field(ge=0, le=100, description="Progress percentage (0 to 100)")
    reason: str = Field(default="Progress updated", description="Reason for update")


class CreateTaskDependencyRequest(BaseModel):
    """Payload model for linking a dependency between tasks."""

    target_task_id: str = Field(description="Task ID that must precede or be completed")
    dependency_type: DependencyType = Field(
        default=DependencyType.DEPENDS_ON, description="Relationship category type"
    )


class CreateTaskGroupRequest(BaseModel):
    """Payload model for creating a task group."""

    owner_id: str = Field(description="User ID owning the task group")
    name: str = Field(description="Display name for the task group")
    description: str = Field(default="", description="Detailed group description")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata")


class UpdateTaskGroupRequest(BaseModel):
    """Payload model for updating a task group."""

    name: str | None = Field(default=None, description="Updated name")
    description: str | None = Field(default=None, description="Updated description")
    status: TaskGroupStatus | None = Field(default=None, description="Updated status")


class ConvertPlanToTasksRequest(BaseModel):
    """Payload model for converting a Module 11 plan into tasks."""

    owner_id: str | None = Field(default=None, description="Override owner ID for generated tasks")
