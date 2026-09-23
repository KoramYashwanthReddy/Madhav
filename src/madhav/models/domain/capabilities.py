"""Declarative model capability metadata model."""

from pydantic import BaseModel, Field


class ModelCapabilities(BaseModel):
    """Declarative capability metadata declared by a model definition."""

    text_generation: bool = Field(default=True, description="Supports text generation")
    chat: bool = Field(default=True, description="Supports conversational chat")
    streaming: bool = Field(default=False, description="Supports streaming token response iterator")
    vision: bool = Field(default=False, description="Supports image/vision input analysis")
    embeddings: bool = Field(default=False, description="Supports vector embedding generation")
    tool_calling: bool = Field(default=False, description="Supports native tool/function calling")
    structured_output: bool = Field(
        default=False, description="Supports schema-constrained JSON output"
    )
    reasoning: bool = Field(default=False, description="Supports chain-of-thought reasoning")
