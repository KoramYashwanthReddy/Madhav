"""Provider-neutral AI inference request domain model."""

import uuid
from typing import Any

from pydantic import BaseModel, Field, field_validator

from madhav.ai.domain.messages import AIMessage
from madhav.ai.domain.parameters import GenerationParameters


class AIRequest(BaseModel):
    """Normalized AI inference execution request."""

    request_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique correlation identifier for AI request",
    )
    messages: list[AIMessage] = Field(description="Ordered conversation context messages")
    generation: GenerationParameters = Field(
        default_factory=GenerationParameters, description="Generation configuration parameters"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata dictionary for execution context"
    )
    timeout: float | None = Field(
        default=None, description="Optional per-request timeout limit in seconds", gt=0.0
    )
    stream: bool = Field(default=False, description="Toggle streaming output iterator mode")

    @field_validator("messages")
    @classmethod
    def validate_messages_not_empty(cls, v: list[AIMessage]) -> list[AIMessage]:
        """Ensure request contains at least one AI message."""
        if not v:
            raise ValueError("AIRequest must contain at least one message.")
        return v
