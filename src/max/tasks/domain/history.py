"""Task history and audit trail record model."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from max.tasks.domain.enums import TaskStatus


class TaskHistoryEntry(BaseModel):
    """Audit entry recording a status transition or major state update on a task."""

    model_config = ConfigDict(frozen=True)

    history_id: str = Field(
        default_factory=lambda: f"hist_{uuid4().hex[:12]}", description="Unique history record ID"
    )
    task_id: str = Field(description="Associated task ID")
    previous_status: TaskStatus | None = Field(default=None, description="Previous status state")
    new_status: TaskStatus = Field(description="New status state")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Event occurrence timestamp"
    )
    reason: str = Field(
        default="State transition", description="Descriptive explanation for change"
    )
    actor: str = Field(
        default="system", description="Entity initiating the update (user, system, mapper)"
    )
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional context or progress details"
    )
