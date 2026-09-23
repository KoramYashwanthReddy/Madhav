"""API response schemas for Module 13 Agent Engine endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from max.agents.domain.agent import AgentCapability, AgentConfiguration, AgentLimits
from max.agents.domain.assignment import AssignmentPriority, AssignmentStatus
from max.agents.domain.enums import AgentExecutionMode, AgentRole, AgentStatus, AgentType
from max.agents.domain.run import AgentFailure, AgentNextAction, AgentResult, AgentRunStatus
from max.agents.domain.trace import AgentEvent


class AgentResponse(BaseModel):
    """API representation of an Agent."""

    id: str = Field(description="Agent unique ID")
    name: str = Field(description="Stable name identifier")
    description: str = Field(description="Agent summary")
    type: AgentType = Field(description="Agent type category")
    role: AgentRole = Field(description="Agent role")
    status: AgentStatus = Field(description="Lifecycle status")
    capabilities: list[AgentCapability] = Field(description="Supported capabilities")
    configuration: AgentConfiguration = Field(description="Model/runtime config")
    limits: AgentLimits = Field(description="Coordination limits")
    owner_id: str = Field(description="Owner user ID")
    metadata: dict[str, Any] = Field(description="Custom metadata")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class AgentAssignmentResponse(BaseModel):
    """API representation of an Agent Assignment."""

    assignment_id: str = Field(description="Assignment unique ID")
    agent_id: str = Field(description="Assigned agent ID")
    task_id: str = Field(description="Module 12 Task ID")
    plan_id: str | None = Field(default=None, description="Module 11 Plan ID")
    status: AssignmentStatus = Field(description="Assignment status")
    priority: AssignmentPriority = Field(description="Priority level")
    reason: str = Field(description="Reason/context")
    metadata: dict[str, Any] = Field(description="Custom metadata")
    assigned_at: datetime = Field(description="Assignment timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class AgentRunResponse(BaseModel):
    """API representation of an Agent Run."""

    run_id: str = Field(description="Run unique ID")
    agent_id: str = Field(description="Executing agent ID")
    task_id: str | None = Field(default=None, description="Task ID")
    plan_id: str | None = Field(default=None, description="Plan ID")
    conversation_id: str | None = Field(default=None, description="Conversation ID")
    owner_id: str = Field(description="Owner user ID")
    status: AgentRunStatus = Field(description="Run lifecycle status")
    execution_mode: AgentExecutionMode = Field(description="Run execution mode")
    retry_count: int = Field(description="Retry attempt count")
    client_request_id: str | None = Field(default=None, description="Idempotency key")
    started_at: datetime | None = Field(default=None, description="Start timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp")
    failure: AgentFailure | None = Field(default=None, description="Failure detail if failed")
    result: AgentResult | None = Field(default=None, description="Result detail if completed")
    next_action: AgentNextAction | None = Field(
        default=None, description="Structured next action intent"
    )
    metadata: dict[str, Any] = Field(description="Custom metadata")
    created_at: datetime = Field(description="Run creation timestamp")


class AgentTraceResponse(BaseModel):
    """API representation of an Agent Run Trace."""

    run_id: str = Field(description="Target run ID")
    events: list[AgentEvent] = Field(description="Chronological event log")
    total_events: int = Field(description="Total event count")


class AgentDelegationResponse(BaseModel):
    """API representation of an Agent Delegation."""

    delegation_id: str = Field(description="Delegation unique ID")
    parent_agent_id: str = Field(description="Parent delegating agent ID")
    child_agent_id: str = Field(description="Child delegated agent ID")
    task_id: str | None = Field(default=None, description="Delegated task ID")
    parent_run_id: str | None = Field(default=None, description="Parent run ID")
    child_run_id: str | None = Field(default=None, description="Child run ID")
    reason: str = Field(description="Delegation rationale")
    status: str = Field(description="Delegation status")
    created_at: datetime = Field(description="Creation timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp")


class AgentSelectionResponse(BaseModel):
    """API representation of an Agent Selection result."""

    selected_agent_id: str | None = Field(default=None, description="Selected agent ID if found")
    selected_agent_name: str | None = Field(
        default=None, description="Selected agent name if found"
    )
    matched: bool = Field(description="Whether a suitable agent was matched")
    reason: str = Field(description="Explanation of selection outcome")
    evaluated_agent_count: int = Field(description="Number of agents evaluated")


class AgentAvailabilityResponse(BaseModel):
    """API representation of Agent Availability."""

    agent_id: str = Field(description="Target agent ID")
    is_available: bool = Field(description="Whether agent has capacity and active state")
    active_runs_count: int = Field(description="Current running count")
    max_concurrent_tasks: int = Field(description="Max allowed concurrent tasks")
    status: AgentStatus = Field(description="Agent status")


class AgentCapabilitiesResponse(BaseModel):
    """API representation of Agent Capabilities."""

    agent_id: str = Field(description="Target agent ID")
    capabilities: list[AgentCapability] = Field(description="List of capabilities")
