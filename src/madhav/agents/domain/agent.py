"""Agent entity, configuration, limits, and boundary intent models."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from madhav.agents.domain.enums import (
    AgentCapability,
    AgentRole,
    AgentStatus,
    AgentType,
    FailureCategory,
    RetryStrategy,
)

__all__ = [
    "Agent",
    "AgentCapability",
    "AgentConfiguration",
    "AgentLimits",
    "AgentReference",
    "AgentRetryPolicy",
    "AgentRole",
    "AgentStatus",
    "AgentType",
    "FailureCategory",
    "PermissionRequestIntent",
    "RetryStrategy",
    "ToolRequestIntent",
]


class AgentLimits(BaseModel):
    """Coordination safety limits governing an agent's run bounds."""

    model_config = ConfigDict(frozen=True)

    max_tasks_per_run: int = Field(default=10, ge=1, description="Maximum tasks handled per run")
    max_steps_per_run: int = Field(default=50, ge=1, description="Maximum coordination steps allowed per run")
    max_delegations: int = Field(default=5, ge=0, description="Maximum sub-delegations allowed per run")
    max_retries: int = Field(default=3, ge=0, description="Maximum run retries permitted")
    max_context_items: int = Field(default=20, ge=1, description="Maximum context package items")
    max_run_duration: float = Field(default=300.0, ge=1.0, description="Maximum run wall-clock duration seconds")
    max_agent_depth: int = Field(default=5, ge=1, description="Maximum nesting depth for sub-delegations")
    max_concurrent_tasks: int = Field(default=5, ge=1, description="Maximum concurrent tasks")


class AgentRetryPolicy(BaseModel):
    """Retry specification metadata for agent runs."""

    model_config = ConfigDict(frozen=True)

    max_retries: int = Field(default=3, ge=0, description="Maximum retries")
    retryable_categories: list[FailureCategory] = Field(
        default_factory=lambda: [FailureCategory.MODEL_ERROR, FailureCategory.TIMEOUT, FailureCategory.TASK_ERROR],
        description="Failure categories eligible for retry",
    )
    backoff_strategy: RetryStrategy = Field(default=RetryStrategy.FIXED, description="Backoff strategy")
    initial_delay: float = Field(default=1.0, ge=0.0, description="Initial retry delay in seconds")
    max_delay: float = Field(default=60.0, ge=0.0, description="Maximum backoff cap in seconds")


class AgentConfiguration(BaseModel):
    """Agent runtime configuration settings (references Module 05 model abstractions)."""

    model_config = ConfigDict(frozen=True)

    model_id: str = Field(default="dev-model-v1", description="Module 05 Model identifier reference")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_output_tokens: int = Field(default=2048, ge=1, description="Token generation limit")
    context_policy: str = Field(default="DEFAULT", description="Context Manager package assembly policy")
    max_concurrent_tasks: int = Field(default=5, ge=1, description="Max concurrent active tasks")
    max_run_duration: float = Field(default=300.0, ge=1.0, description="Run duration cutoff limit")
    retry_policy: AgentRetryPolicy = Field(default_factory=AgentRetryPolicy, description="Retry policy")
    delegation_enabled: bool = Field(default=True, description="Whether agent can delegate tasks to other agents")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary safe config metadata")


class AgentReference(BaseModel):
    """Structured link between an Agent and an external artifact (Task, Plan, Conversation, Memory)."""

    model_config = ConfigDict(frozen=True)

    reference_type: str = Field(description="Artifact category type (PLAN, TASK, CONVERSATION, MEMORY)")
    reference_id: str = Field(description="Unique artifact ID")
    summary: str | None = Field(default=None, description="Optional brief label descriptor")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional reference context")


class ToolRequestIntent(BaseModel):
    """Structured intent representation bridging to Module 14 Tool Registry (NO ACTION EXECUTION)."""

    model_config = ConfigDict(frozen=True)

    intent_id: str = Field(default_factory=lambda: f"tool_req_{uuid4().hex[:12]}")
    run_id: str = Field(description="Originating AgentRun ID")
    agent_id: str = Field(description="Originating Agent ID")
    task_id: str | None = Field(default=None, description="Target task ID")
    requested_capability: str = Field(description="Theoretical capability requested")
    tool_name: str = Field(description="Name of requested tool")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Tool invocation parameters")
    reason: str = Field(default="Tool capability required", description="Reason for request")
    status: str = Field(default="NOT_IMPLEMENTED", description="Boundary status marker")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PermissionRequestIntent(BaseModel):
    """Structured intent representation bridging to Module 15 Permission Engine (NO PERMISSION GRANTED)."""

    model_config = ConfigDict(frozen=True)

    intent_id: str = Field(default_factory=lambda: f"perm_req_{uuid4().hex[:12]}")
    run_id: str = Field(description="Originating AgentRun ID")
    agent_id: str = Field(description="Originating Agent ID")
    task_id: str | None = Field(default=None, description="Target task ID")
    requested_permission: str = Field(description="Permission requested")
    resource: str = Field(description="Target resource descriptor")
    reason: str = Field(default="Permission check required", description="Reason for request")
    status: str = Field(default="NOT_IMPLEMENTED", description="Boundary status marker")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Agent(BaseModel):
    """Core domain entity representing a logical AI worker/coordinator."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: f"agent_{uuid4().hex[:12]}", description="Unique agent identifier")
    owner_id: str = Field(description="User ID owning the agent")
    name: str = Field(description="Stable agent identifier name (e.g. 'planner', 'researcher')")
    description: str = Field(default="", description="Detailed worker description")
    type: AgentType = Field(default=AgentType.GENERAL, description="Worker type classification")
    role: AgentRole = Field(default=AgentRole.ASSISTANT, description="Assigned functional role")
    status: AgentStatus = Field(default=AgentStatus.CREATED, description="Current lifecycle state")
    capabilities: list[AgentCapability] = Field(default_factory=list, description="Claimed capabilities")
    configuration: AgentConfiguration = Field(default_factory=AgentConfiguration, description="Config settings")
    limits: AgentLimits = Field(default_factory=AgentLimits, description="Safety limits")

    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary safe metadata")
