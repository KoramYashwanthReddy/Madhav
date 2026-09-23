"""Agent trace and operational event models (NO private chain-of-thought)."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from madhav.agents.domain.enums import AgentEventType

__all__ = ["AgentEvent", "AgentEventType", "AgentTrace"]


class AgentEvent(BaseModel):
    """Immutable operational trace event (Pure operational audit, NO chain-of-thought text)."""

    model_config = ConfigDict(frozen=True)

    event_id: str = Field(default_factory=lambda: f"evt_{uuid4().hex[:12]}", description="Unique event ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event occurrence timestamp")
    event_type: AgentEventType = Field(description="Operational event taxonomy category")
    agent_id: str = Field(description="Associated Agent ID")
    run_id: str | None = Field(default=None, description="Associated AgentRun ID")
    task_id: str | None = Field(default=None, description="Associated Task ID")
    step_id: str | None = Field(default=None, description="Associated Plan step ID")
    summary: str = Field(description="Human-readable operational summary")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary safe metadata")


class AgentTrace(BaseModel):
    """Aggregate trace audit log container for an AgentRun."""

    model_config = ConfigDict(frozen=False)

    run_id: str = Field(description="Associated AgentRun ID")
    agent_id: str = Field(description="Associated Agent ID")
    events: list[AgentEvent] = Field(default_factory=list, description="Chronological sequence of events")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Trace creation timestamp")

    def record_event(self, event: AgentEvent) -> None:
        """Record an operational trace event."""
        self.events.append(event)
