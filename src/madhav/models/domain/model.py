"""Core Model domain entity aggregate."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from madhav.models.domain.artifact import ModelArtifact
from madhav.models.domain.capabilities import ModelCapabilities
from madhav.models.domain.enums import ModelLifecycleState
from madhav.models.domain.identity import ModelIdentifier
from madhav.models.domain.requirements import ModelRequirements


class Model(BaseModel):
    """Core domain representation of an AI Model definition."""

    identifier: ModelIdentifier = Field(description="Model identity specification")
    capabilities: ModelCapabilities = Field(
        default_factory=ModelCapabilities, description="Declared capabilities"
    )
    requirements: ModelRequirements = Field(
        default_factory=ModelRequirements, description="Hardware/resource requirements"
    )
    artifact: ModelArtifact | None = Field(default=None, description="Model artifact descriptor")
    target_runtime: str = Field(
        default="stub", description="Target Module 04 AI Runtime provider name (e.g. stub, local)"
    )
    lifecycle_state: ModelLifecycleState = Field(
        default=ModelLifecycleState.REGISTERED, description="Current lifecycle state"
    )
    description: str | None = Field(default=None, description="Optional model description")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata key-value pairs")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Model registration timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Last updated timestamp",
    )

    @property
    def model_id(self) -> str:
        """Convenience property for model_id."""
        return self.identifier.model_id

    @property
    def is_available(self) -> bool:
        """Check if model is in available state."""
        return self.lifecycle_state in {
            ModelLifecycleState.AVAILABLE,
            ModelLifecycleState.LOADED,
        }

    @property
    def is_loaded(self) -> bool:
        """Check if model is in loaded state."""
        return self.lifecycle_state == ModelLifecycleState.LOADED

    def transition_to(self, new_state: ModelLifecycleState) -> None:
        """Validate and transition to a new lifecycle state."""
        valid_transitions: dict[ModelLifecycleState, set[ModelLifecycleState]] = {
            ModelLifecycleState.REGISTERED: {
                ModelLifecycleState.AVAILABLE,
                ModelLifecycleState.UNAVAILABLE,
                ModelLifecycleState.FAILED,
            },
            ModelLifecycleState.AVAILABLE: {
                ModelLifecycleState.LOADING,
                ModelLifecycleState.UNAVAILABLE,
                ModelLifecycleState.FAILED,
            },
            ModelLifecycleState.LOADING: {
                ModelLifecycleState.LOADED,
                ModelLifecycleState.FAILED,
                ModelLifecycleState.AVAILABLE,
            },
            ModelLifecycleState.LOADED: {
                ModelLifecycleState.UNLOADING,
                ModelLifecycleState.FAILED,
                ModelLifecycleState.AVAILABLE,
            },
            ModelLifecycleState.UNLOADING: {
                ModelLifecycleState.AVAILABLE,
                ModelLifecycleState.FAILED,
            },
            ModelLifecycleState.UNAVAILABLE: {
                ModelLifecycleState.REGISTERED,
                ModelLifecycleState.AVAILABLE,
                ModelLifecycleState.FAILED,
            },
            ModelLifecycleState.FAILED: {
                ModelLifecycleState.REGISTERED,
                ModelLifecycleState.AVAILABLE,
                ModelLifecycleState.UNAVAILABLE,
            },
        }

        allowed = valid_transitions.get(self.lifecycle_state, set())
        if new_state not in allowed and new_state != self.lifecycle_state:
            raise ValueError(
                f"Invalid lifecycle transition for model '{self.model_id}': "
                f"from '{self.lifecycle_state}' to '{new_state}'."
            )

        self.lifecycle_state = new_state
        self.updated_at = datetime.now(UTC)
