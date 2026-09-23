"""API request DTO models for Context Management endpoints."""

from pydantic import BaseModel, Field, field_validator


class BuildContextRequest(BaseModel):
    """API request payload for building and inspecting a context package."""

    user_request: str = Field(description="Primary user prompt or instruction")
    model_reference: str | None = Field(
        default=None, description="Optional target model identifier (e.g. 'development-stub')"
    )
    policy_name: str | None = Field(
        default="default", description="Context policy preset ('default', 'minimal', 'full')"
    )
    allow_sensitive_identity: bool = Field(
        default=False, description="Opt-in flag permitting sensitive identity attributes"
    )
    custom_max_tokens: int | None = Field(
        default=None, description="Optional override max context token capacity", gt=0
    )

    @field_validator("user_request")
    @classmethod
    def validate_user_request_not_empty(cls, v: str) -> str:
        """Ensure user request string is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("user_request cannot be empty or whitespace-only.")
        return v.strip()
