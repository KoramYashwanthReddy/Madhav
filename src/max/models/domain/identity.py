"""Model identity domain entity."""

from pydantic import BaseModel, Field

from max.models.domain.enums import ModelProvider


class ModelIdentifier(BaseModel):
    """Stable identity representation for a model."""

    model_id: str = Field(description="Unique canonical model identifier (e.g. 'development-stub')")
    provider: ModelProvider = Field(description="Model provider or ecosystem identifier")
    name: str = Field(description="Human-readable model name")
    version: str = Field(default="1.0.0", description="Model semantic version string")
    revision: str | None = Field(
        default=None, description="Optional revision string or commit hash"
    )

    @property
    def canonical_id(self) -> str:
        """Return canonical identifier string."""
        return self.model_id
