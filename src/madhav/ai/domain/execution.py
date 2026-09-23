"""Execution metadata domain model."""

from datetime import datetime

from pydantic import BaseModel, Field


class AIExecutionMetadata(BaseModel):
    """Execution telemetry and runtime timing metadata."""

    started_at: datetime = Field(description="UTC timestamp when inference execution started")
    completed_at: datetime = Field(description="UTC timestamp when inference execution completed")
    duration_ms: float = Field(
        description="Execution duration in milliseconds measured via monotonic clock"
    )
    provider: str = Field(description="Runtime provider identifier used for execution")
    model: str = Field(description="Model reference identifier used for execution")
    request_id: str = Field(description="Correlation request identifier")
    stream: bool = Field(description="Boolean flag indicating if streaming mode was used")
    success: bool = Field(description="Boolean flag indicating execution success")
