"""Inter-agent delegation domain model."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from max.agents.domain.enums import DelegationStatus


class AgentDelegation(BaseModel):
    """Entity representing a sub-delegation relationship from a parent agent to a child agent."""

    model_config = ConfigDict(frozen=True)

    delegation_id: str = Field(
        default_factory=lambda: f"dlg_{uuid4().hex[:12]}", description="Unique delegation ID"
    )
    parent_agent_id: str = Field(description="Parent Agent ID initiating delegation")
    child_agent_id: str = Field(description="Child Agent ID receiving delegation")
    parent_run_id: str | None = Field(default=None, description="Parent AgentRun ID")
    child_run_id: str | None = Field(default=None, description="Child AgentRun ID")
    task_id: str | None = Field(default=None, description="Delegated Task ID")
    reason: str = Field(default="Subtask delegation", description="Reason for delegation")
    status: DelegationStatus = Field(
        default=DelegationStatus.REQUESTED, description="Delegation status"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary delegation metadata"
    )
