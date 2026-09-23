"""ContextBudget domain model for computing and enforcing input token limits."""

from pydantic import BaseModel, Field, model_validator


class ContextBudget(BaseModel):
    """Token budget constraints calculated for model context input allocation."""

    max_tokens: int = Field(
        description="Total context token window capacity of the target model", gt=0
    )
    reserved_tokens: int = Field(
        default=1024, description="Tokens reserved for model generation output", ge=0
    )
    safety_margin: int = Field(
        default=256, description="Safety buffer tokens reserved to prevent model overflow", ge=0
    )

    @model_validator(mode="after")
    def validate_budget_bounds(self) -> "ContextBudget":
        """Ensure reserved tokens and safety margin do not exceed total capacity."""
        if (self.reserved_tokens + self.safety_margin) >= self.max_tokens:
            msg = (
                f"Combined reserved output ({self.reserved_tokens}) and "
                f"safety margin ({self.safety_margin}) must be less than "
                f"model max tokens ({self.max_tokens})."
            )
            raise ValueError(msg)
        return self


    @property
    def available_input_tokens(self) -> int:
        """Calculate net available input budget for context selection."""
        return max(0, self.max_tokens - self.reserved_tokens - self.safety_margin)
