"""Structured reference linkage between Tasks and external system artifacts."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from max.tasks.domain.enums import TaskReferenceType


class TaskReference(BaseModel):
    """Structured pointer referencing an upstream artifact (Plan, Conversation, Memory, etc.)."""

    model_config = ConfigDict(frozen=True)

    reference_type: TaskReferenceType = Field(description="Type of referenced artifact")
    reference_id: str = Field(description="Unique ID of referenced artifact")
    summary: str | None = Field(default=None, description="Optional brief label or text summary")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional contextual metadata"
    )
