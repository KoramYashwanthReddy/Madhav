"""Tool audit trace events and operational log entities."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from madhav.tools.domain.enums import ToolEventType


class ToolEvent(BaseModel):
    """Immutable operational event recorded during tool or invocation lifecycle."""

    model_config = ConfigDict(frozen=True)

    event_id: str = Field(
        default_factory=lambda: f"evt_{uuid4().hex[:12]}", description="Unique event ID"
    )
    event_type: ToolEventType = Field(description="Structured event classification type")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")

    tool_id: str | None = Field(default=None, description="Associated Tool ID")
    invocation_id: str | None = Field(default=None, description="Associated Invocation ID")
    agent_id: str | None = Field(default=None, description="Calling Agent ID")
    run_id: str | None = Field(default=None, description="Calling AgentRun ID")
    task_id: str | None = Field(default=None, description="Linked Task ID")

    summary: str = Field(description="Operational event summary text")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Event context metadata")


class ToolTrace(BaseModel):
    """Aggregated operational trace audit trail for a tool invocation."""

    model_config = ConfigDict(frozen=True)

    invocation_id: str = Field(description="Invocation identifier")
    events: list[ToolEvent] = Field(default_factory=list, description="Ordered timeline of operational events")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Trace creation timestamp")
