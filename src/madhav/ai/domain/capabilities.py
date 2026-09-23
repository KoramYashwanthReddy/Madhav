"""Runtime capabilities and health status domain models."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from madhav.ai.domain.enums import RuntimeHealthStatus


class RuntimeCapabilities(BaseModel):
    """Declared features and capabilities of an AI model runtime adapter."""

    generation: bool = Field(default=True, description="Supports text generation")
    streaming: bool = Field(default=True, description="Supports streaming response iteration")
    token_usage: bool = Field(default=False, description="Provides token count telemetry")
    cancellation: bool = Field(default=True, description="Supports in-flight request cancellation")
    structured_output: bool = Field(default=False, description="Supports JSON schema enforcement")
    vision: bool = Field(default=False, description="Supports multi-modal image inputs")
    tool_calling: bool = Field(default=False, description="Supports function/tool calling")


class RuntimeStatus(BaseModel):
    """Runtime operational status and health diagnostic report."""

    status: RuntimeHealthStatus = Field(
        default=RuntimeHealthStatus.AVAILABLE, description="Current health status enum"
    )
    provider: str = Field(description="Runtime provider identifier")
    model: str = Field(description="Active model reference string")
    message: str = Field(default="Runtime is operational.", description="Diagnostic status message")
    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Check UTC timestamp",
    )
