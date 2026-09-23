"""Normalized diagnostic status domain entity for models."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from max.models.domain.capabilities import ModelCapabilities
from max.models.domain.enums import ModelFormat, ModelLifecycleState, ModelProvider


class ModelStatus(BaseModel):
    """Diagnostic status snapshot for a registered model."""

    model_id: str = Field(description="Unique model identifier")
    provider: ModelProvider = Field(description="Model provider")
    lifecycle_state: ModelLifecycleState = Field(description="Current lifecycle state")
    is_available: bool = Field(description="Indicates model artifact/runtime is available")
    is_loaded: bool = Field(description="Indicates model is currently loaded in memory/runtime")
    target_runtime: str = Field(description="Target Module 04 AI Runtime provider identifier")
    capabilities: ModelCapabilities = Field(description="Declared capability matrix")
    format: ModelFormat = Field(description="Model artifact format")
    artifact_path: str | None = Field(
        default=None, description="Artifact filesystem location path if local"
    )
    error_message: str | None = Field(default=None, description="Error message if in FAILED state")
    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Status snapshot timestamp",
    )
