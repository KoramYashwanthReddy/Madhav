"""API response DTO schemas for Model Management endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from max.models.domain.enums import ModelFormat, ModelLifecycleState, ModelProvider
from max.models.schemas.requests import (
    ModelArtifactSchema,
    ModelCapabilitiesSchema,
    ModelRequirementsSchema,
)


class ModelResponse(BaseModel):
    """API payload response representing a model definition."""

    model_id: str = Field(description="Unique model identifier")
    provider: ModelProvider = Field(description="Model provider name")
    name: str = Field(description="Display name")
    version: str = Field(description="Version string")
    revision: str | None = Field(default=None, description="Revision string")
    capabilities: ModelCapabilitiesSchema = Field(description="Capabilities matrix")
    requirements: ModelRequirementsSchema = Field(description="Resource requirements")
    artifact: ModelArtifactSchema | None = Field(default=None, description="Artifact descriptor")
    target_runtime: str = Field(description="Target AI Runtime provider")
    lifecycle_state: ModelLifecycleState = Field(description="Current lifecycle state")
    description: str | None = Field(default=None, description="Model description")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")
    created_at: datetime = Field(description="Registration timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class ModelListResponse(BaseModel):
    """API response container listing model definitions."""

    models: list[ModelResponse] = Field(description="List of registered model definitions")
    total: int = Field(description="Total count of models")


class ModelStatusResponse(BaseModel):
    """API response container for model status query."""

    model_id: str = Field(description="Model identifier")
    provider: ModelProvider = Field(description="Provider identifier")
    lifecycle_state: ModelLifecycleState = Field(description="Current lifecycle state")
    is_available: bool = Field(description="Is model available")
    is_loaded: bool = Field(description="Is model loaded")
    target_runtime: str = Field(description="Target runtime identifier")
    capabilities: ModelCapabilitiesSchema = Field(description="Declared capabilities")
    format: ModelFormat = Field(description="Artifact format")
    artifact_path: str | None = Field(default=None, description="Artifact path string")
    error_message: str | None = Field(default=None, description="Error message if failed")
    checked_at: datetime = Field(description="Status check timestamp")


class ModelVerifyResponse(BaseModel):
    """API response container for model artifact checksum verification."""

    model_id: str = Field(description="Model identifier")
    verified: bool = Field(description="Checksum verification status")
    checksum_algorithm: str = Field(description="Algorithm used")
    message: str = Field(description="Verification result summary")
