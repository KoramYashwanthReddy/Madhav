"""Provider-neutral generation configuration parameters."""

from pydantic import BaseModel, Field, field_validator


class GenerationParameters(BaseModel):
    """Configuration parameters controlling AI text generation."""

    temperature: float = Field(
        default=0.7, description="Sampling temperature (0.0 to 2.0)", ge=0.0, le=2.0
    )
    top_p: float = Field(
        default=1.0, description="Nucleus sampling top_p probability (0.0 to 1.0)", ge=0.0, le=1.0
    )
    max_tokens: int = Field(
        default=1024, description="Maximum number of tokens to generate", ge=1, le=128000
    )
    stop_sequences: list[str] | None = Field(
        default=None, description="Optional stop sequences for generation process"
    )

    @field_validator("stop_sequences")
    @classmethod
    def validate_stop_sequences(cls, v: list[str] | None) -> list[str] | None:
        """Validate stop sequence elements if provided."""
        if v is not None:
            for seq in v:
                if not seq:
                    raise ValueError("Stop sequence cannot be empty string.")
        return v
