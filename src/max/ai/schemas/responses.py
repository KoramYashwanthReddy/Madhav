"""API response schemas for AI Runtime endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field

from max.ai.domain.enums import FinishReason, RuntimeHealthStatus


class AIUsageSchema(BaseModel):
    """Schema for token usage statistics."""

    input_tokens: int | None = Field(default=None, description="Input token count")
    output_tokens: int | None = Field(default=None, description="Output token count")
    total_tokens: int | None = Field(default=None, description="Total token count")


class AIExecutionMetadataSchema(BaseModel):
    """Schema for execution telemetry metadata."""

    started_at: datetime = Field(description="Execution start UTC timestamp")
    completed_at: datetime = Field(description="Execution completion UTC timestamp")
    duration_ms: float = Field(description="Execution duration in milliseconds")
    provider: str = Field(description="Runtime provider identifier")
    model: str = Field(description="Model reference string")
    request_id: str = Field(description="Correlation request_id")
    stream: bool = Field(description="Streaming flag")
    success: bool = Field(description="Success flag")


class AIGenerateResponse(BaseModel):
    """API response payload for generation endpoint."""

    request_id: str = Field(description="Correlation request identifier")
    content: str = Field(description="Generated text content payload")
    finish_reason: FinishReason = Field(description="Generation finish reason")
    usage: AIUsageSchema = Field(description="Token usage metrics")
    execution: AIExecutionMetadataSchema = Field(description="Execution telemetry")
    model_reference: str = Field(description="Model reference identifier")
    provider: str = Field(description="Provider identifier string")
    created_at: datetime = Field(description="Response creation UTC timestamp")


class RuntimeStatusResponse(BaseModel):
    """API response payload for runtime health status."""

    status: RuntimeHealthStatus = Field(description="Runtime health status enum")
    provider: str = Field(description="Provider identifier")
    model: str = Field(description="Model reference identifier")
    message: str = Field(description="Diagnostic message")
    checked_at: datetime = Field(description="Check UTC timestamp")


class RuntimeCapabilitiesResponse(BaseModel):
    """API response payload for declared runtime capabilities."""

    generation: bool = Field(description="Supports text generation")
    streaming: bool = Field(description="Supports streaming")
    token_usage: bool = Field(description="Supports token telemetry")
    cancellation: bool = Field(description="Supports in-flight cancellation")
    structured_output: bool = Field(description="Supports structured output schemas")
    vision: bool = Field(description="Supports multi-modal vision inputs")
    tool_calling: bool = Field(description="Supports function/tool calling")
