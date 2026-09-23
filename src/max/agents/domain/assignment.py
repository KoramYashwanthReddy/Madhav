"""Agent task assignment domain entity."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from max.agents.domain.enums import AssignmentPriority, AssignmentStatus

__all__ = ["AgentAssignment", "AssignmentPriority", "AssignmentStatus"]


class AgentAssignment(BaseModel):
    """Entity representing the link between an Agent and an assigned Task."""

    model_config = ConfigDict(frozen=True)

    assignment_id: str = Field(
        default_factory=lambda: f"asgn_{uuid4().hex[:12]}", description="Unique assignment ID"
    )
    agent_id: str = Field(description="Assigned Agent ID")
    task_id: str = Field(description="Assigned Module 12 Task ID")
    plan_id: str | None = Field(default=None, description="Linked Module 11 Plan ID")
    owner_id: str = Field(default="", description="User ID owning the assignment")
    assigned_at: datetime = Field(
        default_factory=datetime.utcnow, description="Assignment timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last updated timestamp"
    )
    status: AssignmentStatus = Field(
        default=AssignmentStatus.ASSIGNED, description="Assignment status"
    )
    priority: AssignmentPriority = Field(
        default=AssignmentPriority.NORMAL, description="Task priority label"
    )
    reason: str = Field(default="Task assignment", description="Reason for assignment")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary assignment metadata"
    )
