"""API request schemas for Module 13 Agent Engine endpoints."""

from typing import Any

from pydantic import BaseModel, Field

from max.agents.domain.agent import AgentCapability, AgentConfiguration, AgentLimits
from max.agents.domain.assignment import AssignmentPriority
from max.agents.domain.enums import AgentExecutionMode, AgentRole, AgentType


class CreateAgentRequest(BaseModel):
    """Request schema for creating a new Agent."""

    name: str = Field(description="Stable name identifier for the agent")
    description: str = Field(default="", description="Detailed summary of agent responsibilities")
    type: AgentType = Field(default=AgentType.GENERAL, description="Category type of agent")
    role: AgentRole = Field(default=AgentRole.ASSISTANT, description="Functional role")
    capabilities: list[AgentCapability] = Field(
        default_factory=list, description="Supported capabilities"
    )
    configuration: AgentConfiguration = Field(
        default_factory=AgentConfiguration, description="Model and run settings"
    )
    limits: AgentLimits = Field(
        default_factory=AgentLimits, description="Safety and coordination limits"
    )
    owner_id: str = Field(description="User ID owning this agent")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata")


class UpdateAgentRequest(BaseModel):
    """Request schema for updating an existing Agent."""

    name: str | None = Field(default=None, description="Updated name")
    description: str | None = Field(default=None, description="Updated description")
    type: AgentType | None = Field(default=None, description="Updated type")
    role: AgentRole | None = Field(default=None, description="Updated role")
    capabilities: list[AgentCapability] | None = Field(
        default=None, description="Updated capabilities list"
    )
    configuration: AgentConfiguration | None = Field(
        default=None, description="Updated configuration"
    )
    limits: AgentLimits | None = Field(default=None, description="Updated safety limits")
    metadata: dict[str, Any] | None = Field(default=None, description="Metadata key-values to update")


class CreateAssignmentRequest(BaseModel):
    """Request schema for assigning a task to an agent."""

    task_id: str = Field(description="Module 12 Task ID to assign")
    plan_id: str | None = Field(default=None, description="Module 11 Plan ID if applicable")
    priority: AssignmentPriority = Field(
        default=AssignmentPriority.NORMAL, description="Assignment priority level"
    )
    reason: str = Field(default="", description="Reason or context for assignment")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom assignment metadata")


class CreateRunRequest(BaseModel):
    """Request schema for starting an agent execution run."""

    task_id: str | None = Field(default=None, description="Module 12 Task ID")
    plan_id: str | None = Field(default=None, description="Module 11 Plan ID")
    conversation_id: str | None = Field(default=None, description="Module 07 Conversation ID")
    owner_id: str = Field(description="User ID owning this run")
    execution_mode: AgentExecutionMode = Field(
        default=AgentExecutionMode.DRY_RUN, description="Mode of run execution"
    )
    client_request_id: str | None = Field(
        default=None, description="Idempotency key to prevent duplicate runs"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Run metadata")


class CreateDelegationRequest(BaseModel):
    """Request schema for creating an agent delegation."""

    child_agent_id: str = Field(description="Target agent ID receiving delegated task")
    task_id: str = Field(description="Task ID being delegated")
    parent_run_id: str | None = Field(default=None, description="Originating agent run ID")
    reason: str = Field(default="", description="Reason for delegation")


class SelectAgentRequest(BaseModel):
    """Request schema for selecting an agent based on task requirements."""

    required_capabilities: list[AgentCapability] = Field(
        default_factory=list, description="Capabilities mandatory for selection"
    )
    task_type: str | None = Field(default=None, description="Optional task category filter")
    priority: str | None = Field(default=None, description="Optional priority hint")
    preferred_role: AgentRole | None = Field(default=None, description="Role preference")
    preferred_type: AgentType | None = Field(default=None, description="Type preference")
