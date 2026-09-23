"""Provider-neutral AI message domain model."""

from pydantic import BaseModel, Field, field_validator

from madhav.ai.domain.enums import AIRole


class AIMessage(BaseModel):
    """Provider-neutral AI message representation."""

    role: AIRole = Field(description="Role of message sender (system, user, assistant)")
    content: str = Field(description="Text content of message")

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        """Ensure message content is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty or whitespace-only.")
        return v
