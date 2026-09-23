"""AgentRun execution entity, results, failures, and coordination response models."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from max.agents.domain.agent import PermissionRequestIntent, ToolRequestIntent
from max.agents.domain.enums import (
    AgentExecutionMode,
    AgentRunStatus,
    FailureCategory,
    NextAction,
    RetryStrategy,
)

AgentNextAction = NextAction
AgentNextActionType = NextAction
RetryBackoffStrategy = RetryStrategy

__all__ = [
    "AgentCoordinationRequest",
    "AgentCoordinationResponse",
    "AgentFailure",
    "AgentNextAction",
    "AgentNextActionType",
    "AgentResult",
    "AgentRetryPolicy",
    "AgentRun",
    "AgentRunStatus",
    "RetryBackoffStrategy",
]


class AgentRetryPolicy(BaseModel):
    """Configuration for deterministic retry backoff strategy."""

    model_config = ConfigDict(frozen=True)

    max_retries: int = Field(default=3, ge=0, description="Max allowed retries")
    retryable_categories: list[FailureCategory] = Field(
        default_factory=lambda: [
            FailureCategory.CONTEXT_ERROR,
            FailureCategory.MODEL_ERROR,
            FailureCategory.TIMEOUT,
        ],
        description="Failure categories eligible for retry",
    )
    backoff_strategy: RetryStrategy = Field(
        default=RetryStrategy.EXPONENTIAL, description="Backoff strategy"
    )
    initial_delay_seconds: float = Field(
        default=1.0, ge=0.0, description="Initial delay in seconds"
    )
    max_delay_seconds: float = Field(
        default=60.0, ge=0.0, description="Max delay ceiling in seconds"
    )

    def calculate_delay(self, retry_attempt: int) -> float:
        if self.backoff_strategy == RetryStrategy.NONE:
            return 0.0
        elif self.backoff_strategy == RetryStrategy.FIXED:
            return float(min(self.initial_delay_seconds, self.max_delay_seconds))
        else:
            delay = self.initial_delay_seconds * (2 ** (retry_attempt - 1))
            return float(min(delay, self.max_delay_seconds))

    def should_retry(self, retry_count: int, failure_category: str | FailureCategory) -> bool:
        if retry_count >= self.max_retries:
            return False
        cat_str = (
            failure_category.value
            if isinstance(failure_category, FailureCategory)
            else failure_category
        )
        allowed_cats = {c.value for c in self.retryable_categories}
        return cat_str in allowed_cats


class AgentFailure(BaseModel):
    """Structured failure diagnosis for an AgentRun."""

    model_config = ConfigDict(frozen=True)

    error_code: str = Field(default="AGENT_RUN_FAILED", description="Error taxonomy code")
    message: str = Field(description="Descriptive failure message")
    category: FailureCategory = Field(
        default=FailureCategory.INTERNAL_ERROR, description="Failure category taxonomy"
    )
    retryable: bool = Field(default=True, description="Whether failure permits retry")
    occurred_at: datetime = Field(default_factory=datetime.utcnow, description="Failure timestamp")
    task_id: str | None = Field(default=None, description="Associated task ID")
    step_id: str | None = Field(default=None, description="Associated plan step ID")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Context metadata")


class AgentResult(BaseModel):
    """Structured outcome data produced upon AgentRun completion."""

    model_config = ConfigDict(frozen=True)

    status: AgentRunStatus = Field(default=AgentRunStatus.COMPLETED, description="Run status")
    summary: str = Field(
        default="Agent run completed successfully", description="Human-readable execution summary"
    )
    output_reference: str | None = Field(default=None, description="Pointer to generated artifact")
    completed_tasks: list[str] = Field(
        default_factory=list, description="IDs of tasks completed during run"
    )
    failed_tasks: list[str] = Field(
        default_factory=list, description="IDs of tasks failed during run"
    )
    observations: list[str] = Field(
        default_factory=list, description="Structured operational observations"
    )
    artifacts: list[dict[str, Any]] = Field(
        default_factory=list, description="Structured artifact descriptors"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary output metadata")


class AgentRun(BaseModel):
    """Core domain entity representing one coordinated agent execution run lifecycle."""

    model_config = ConfigDict(frozen=True)

    run_id: str = Field(
        default_factory=lambda: f"run_{uuid4().hex[:12]}", description="Unique run identifier"
    )
    agent_id: str = Field(description="Agent ID assigned to this run")
    task_id: str | None = Field(default=None, description="Linked Module 12 Task ID")
    plan_id: str | None = Field(default=None, description="Linked Module 11 Plan ID")
    plan_step_id: str | None = Field(default=None, description="Linked Plan step ID")
    conversation_id: str | None = Field(default=None, description="Linked Conversation ID")
    owner_id: str = Field(description="User ID owning the run")

    status: AgentRunStatus = Field(default=AgentRunStatus.CREATED, description="Run status")
    execution_mode: AgentExecutionMode = Field(
        default=AgentExecutionMode.DRY_RUN, description="Execution mode"
    )
    client_request_id: str | None = Field(default=None, description="Idempotency key")

    started_at: datetime | None = Field(default=None, description="Run start timestamp")
    completed_at: datetime | None = Field(default=None, description="Run completion timestamp")

    result: AgentResult | None = Field(default=None, description="Outcome result if run completed")
    failure: AgentFailure | None = Field(
        default=None, description="Failure diagnostic if run failed"
    )
    retry_count: int = Field(default=0, ge=0, description="Current retry attempt count")

    next_action: NextAction = Field(
        default=NextAction.COMPLETE, description="Intended next action intent"
    )
    tool_requests: list[ToolRequestIntent] = Field(
        default_factory=list, description="Structured tool request intents"
    )
    permission_requests: list[PermissionRequestIntent] = Field(
        default_factory=list, description="Structured permission request intents"
    )

    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary run metadata")


class AgentCoordinationRequest(BaseModel):
    """Request DTO to initiate agent task coordination."""

    model_config = ConfigDict(frozen=True)

    owner_id: str = Field(description="User ID requesting coordination")
    agent_id: str | None = Field(
        default=None, description="Explicit target Agent ID or None for auto-selection"
    )
    task_id: str | None = Field(default=None, description="Module 12 Task ID")
    plan_id: str | None = Field(default=None, description="Module 11 Plan ID")
    plan_step_id: str | None = Field(default=None, description="Plan step ID")
    conversation_id: str | None = Field(default=None, description="Conversation ID")
    objective: str = Field(default="Coordinate assigned task", description="Run objective text")
    constraints: list[str] = Field(default_factory=list, description="Constraints text list")
    context_reference: str | None = Field(default=None, description="Context reference ID")
    execution_mode: AgentExecutionMode = Field(
        default=AgentExecutionMode.DRY_RUN, description="Execution mode"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary request metadata")


class AgentCoordinationResponse(BaseModel):
    """Response DTO produced after agent task coordination."""

    model_config = ConfigDict(frozen=True)

    run_id: str = Field(description="AgentRun ID")
    agent_id: str = Field(description="Agent ID")
    task_id: str | None = Field(default=None, description="Task ID")
    status: AgentRunStatus = Field(description="Final run status")
    result: AgentResult | None = Field(default=None, description="Outcome result")
    failure: AgentFailure | None = Field(default=None, description="Failure diagnostic if failed")
    next_action: NextAction = Field(description="NextAction intent")
    tool_requests: list[ToolRequestIntent] = Field(
        default_factory=list, description="Tool request intents"
    )
    permission_requests: list[PermissionRequestIntent] = Field(
        default_factory=list, description="Permission request intents"
    )
    trace_reference: str = Field(description="Pointer to trace audit trail")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Response metadata")
