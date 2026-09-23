"""Task group domain entity and summary data structures."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from max.tasks.domain.enums import TaskGroupStatus


class TaskGroup(BaseModel):
    """Entity organizing a collection of related tasks under a shared project/topic."""

    model_config = ConfigDict(frozen=True)

    group_id: str = Field(
        default_factory=lambda: f"grp_{uuid4().hex[:12]}", description="Unique task group ID"
    )
    owner_id: str = Field(description="User ID owning the task group")
    name: str = Field(description="Display name of task group")
    description: str = Field(default="", description="Detailed group description")
    status: TaskGroupStatus = Field(
        default=TaskGroupStatus.ACTIVE, description="Current status of group"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary metadata attributes"
    )


class TaskGroupSummary(BaseModel):
    """Aggregate progress summary for a task group."""

    model_config = ConfigDict(frozen=True)

    group_id: str = Field(description="Task group ID")
    name: str = Field(description="Group display name")
    total_tasks: int = Field(ge=0, description="Total tasks in group")
    completed_tasks: int = Field(ge=0, description="Completed task count")
    pending_tasks: int = Field(ge=0, description="Pending/Ready task count")
    blocked_tasks: int = Field(ge=0, description="Blocked task count")
    in_progress_tasks: int = Field(ge=0, description="In-progress task count")
    overall_progress: float = Field(ge=0.0, le=100.0, description="Weighted progress percentage")
