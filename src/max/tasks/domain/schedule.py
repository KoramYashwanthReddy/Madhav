"""Task schedule and recurrence domain value objects (Future-ready metadata)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from max.tasks.domain.enums import RecurrenceType


class TaskRecurrence(BaseModel):
    """Metadata describing recurring task rules (No background execution in Module 12)."""

    model_config = ConfigDict(frozen=True)

    type: RecurrenceType = Field(description="Recurrence pattern type")
    interval: int = Field(default=1, ge=1, description="Interval step count (e.g. every 2 weeks)")
    until: datetime | None = Field(default=None, description="Optional expiration cutoff date")
    cron_expression: str | None = Field(default=None, description="Optional custom cron expression for CUSTOM type")


class TaskSchedule(BaseModel):
    """Task timing and schedule metadata abstraction."""

    model_config = ConfigDict(frozen=True)

    scheduled_at: datetime | None = Field(default=None, description="Intended start time")
    due_at: datetime | None = Field(default=None, description="Explicit deadline cutoff")
    timezone: str = Field(default="UTC", description="Timezone identifier")
    recurrence: TaskRecurrence | None = Field(default=None, description="Optional recurrence specification")
