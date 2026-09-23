"""AI token usage metadata domain model."""

from pydantic import BaseModel, Field


class AIUsage(BaseModel):
    """Normalized token usage statistics for an inference execution."""

    input_tokens: int | None = Field(
        default=None, description="Prompt/input token count, or None if unavailable"
    )
    output_tokens: int | None = Field(
        default=None, description="Generated output token count, or None if unavailable"
    )
    total_tokens: int | None = Field(
        default=None, description="Total token count, or None if unavailable"
    )
