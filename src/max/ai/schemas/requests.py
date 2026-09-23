"""API request schemas for AI Runtime endpoints."""

from typing import Any

from pydantic import BaseModel, Field

from max.ai.domain.enums import AIRole


class AIMessageSchema(BaseModel):
    """Schema for individual conversation message."""

    role: AIRole = Field(description="Role of message sender (system, user, assistant)")
    content: str = Field(description="Text content of message")


class GenerationParametersSchema(BaseModel):
    """Schema for generation parameter configurations."""

    temperature: float = Field(
        default=0.7, description="Sampling temperature (0.0 to 2.0)", ge=0.0, le=2.0
    )
    top_p: float = Field(
        default=1.0, description="Nucleus sampling top_p (0.0 to 1.0)", ge=0.0, le=1.0
    )
    max_tokens: int = Field(default=1024, description="Maximum response tokens", gt=0)
    stop_sequences: list[str] | None = Field(default=None, description="Stop sequences list")


class AIGenerateRequest(BaseModel):
    """API request payload for text generation endpoint."""

    messages: list[AIMessageSchema] = Field(
        description="List of conversation context messages", min_length=1
    )
    generation: GenerationParametersSchema = Field(
        default_factory=GenerationParametersSchema, description="Generation parameters"
    )
    model: str | None = Field(
        default=None, description="Optional target model identifier (e.g. 'development-stub')"
    )
    provider: str | None = Field(
        default=None, description="Optional target runtime provider override"
    )
    timeout: float | None = Field(
        default=None, description="Optional execution timeout override in seconds"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")
