"""Provider-neutral AI response and streaming event domain models."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from max.ai.domain.enums import FinishReason, StreamEventType
from max.ai.domain.execution import AIExecutionMetadata
from max.ai.domain.usage import AIUsage


class AIResponse(BaseModel):
    """Normalized AI inference response."""

    request_id: str = Field(description="Unique correlation request identifier")
    content: str = Field(description="Generated text content payload")
    finish_reason: FinishReason = Field(
        default=FinishReason.STOP, description="Normalized finish reason code"
    )
    usage: AIUsage = Field(default_factory=AIUsage, description="Token usage statistics")
    execution: AIExecutionMetadata = Field(description="Runtime execution telemetry metadata")
    model_reference: str = Field(description="Model identifier reference")
    provider: str = Field(description="Provider identifier string")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Response creation UTC timestamp",
    )


class AIStreamEvent(BaseModel):
    """Provider-neutral streaming event chunk."""

    event_type: StreamEventType = Field(
        description="Event type indicator (started, delta, completed, error)"
    )
    content_delta: str | None = Field(default=None, description="Incremental text content chunk")
    metadata: dict[str, Any] | None = Field(default=None, description="Event metadata payload")
    completed: bool = Field(default=False, description="Flag indicating final streaming chunk")
