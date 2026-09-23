"""API request DTO schemas for Model Management endpoints."""

from typing import Any

from pydantic import BaseModel, Field

from madhav.models.domain.enums import ModelFormat, ModelProvider


class ModelCapabilitiesSchema(BaseModel):
    """Schema for declaring model capabilities."""

    text_generation: bool = Field(default=True, description="Supports text generation")
    chat: bool = Field(default=True, description="Supports conversational chat")
    streaming: bool = Field(default=False, description="Supports streaming token response iterator")
    vision: bool = Field(default=False, description="Supports vision analysis")
    embeddings: bool = Field(default=False, description="Supports vector embedding generation")
    tool_calling: bool = Field(default=False, description="Supports native tool/function calling")
    structured_output: bool = Field(
        default=False, description="Supports schema-constrained JSON output"
    )
    reasoning: bool = Field(default=False, description="Supports reasoning chain")


class ModelRequirementsSchema(BaseModel):
    """Schema for model resource requirements."""

    minimum_ram_gb: float = Field(default=1.0, description="Minimum RAM in GB", ge=0.0)
    recommended_ram_gb: float = Field(default=2.0, description="Recommended RAM in GB", ge=0.0)
    minimum_vram_gb: float = Field(default=0.0, description="Minimum VRAM in GB", ge=0.0)
    recommended_vram_gb: float = Field(default=0.0, description="Recommended VRAM in GB", ge=0.0)
    cpu_required: bool = Field(default=True, description="Can execute on CPU")
    gpu_required: bool = Field(default=False, description="Requires dedicated GPU")
    supported_gpu_vendor: str | None = Field(default=None, description="Target GPU vendor")
    context_length: int = Field(default=4096, description="Max context length", gt=0)
    parameter_count: str | None = Field(default=None, description="Parameter scale descriptor")


class ModelArtifactSchema(BaseModel):
    """Schema for model artifact specification."""

    format: ModelFormat = Field(default=ModelFormat.UNKNOWN, description="Storage format")
    path: str | None = Field(default=None, description="Artifact filesystem path")
    size_bytes: int | None = Field(default=None, description="File size in bytes", ge=0)
    checksum: str | None = Field(default=None, description="Checksum hash string")
    checksum_algorithm: str = Field(default="sha256", description="Checksum algorithm name")


class ModelRegisterRequest(BaseModel):
    """Request payload for registering a new model definition."""

    model_id: str = Field(description="Unique model identifier (e.g. 'local-llama-3-8b')")
    provider: ModelProvider = Field(
        default=ModelProvider.LOCAL, description="Model provider/ecosystem"
    )
    name: str = Field(description="Human-readable model display name")
    version: str = Field(default="1.0.0", description="Semantic version string")
    revision: str | None = Field(default=None, description="Optional revision tag")
    capabilities: ModelCapabilitiesSchema = Field(
        default_factory=ModelCapabilitiesSchema, description="Declared model capabilities"
    )
    requirements: ModelRequirementsSchema = Field(
        default_factory=ModelRequirementsSchema, description="Declared resource requirements"
    )
    artifact: ModelArtifactSchema | None = Field(default=None, description="Artifact specification")
    target_runtime: str = Field(default="stub", description="Target Module 04 AI Runtime provider")
    description: str | None = Field(default=None, description="Model description text")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata key-value pairs")


class ModelUpdateRequest(BaseModel):
    """Request payload for updating an existing model definition."""

    description: str | None = Field(default=None, description="Updated model description")
    target_runtime: str | None = Field(default=None, description="Updated target runtime provider")
    metadata: dict[str, Any] | None = Field(default=None, description="Updated metadata dictionary")
