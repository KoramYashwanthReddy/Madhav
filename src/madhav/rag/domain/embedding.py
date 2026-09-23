"""Embedding domain model for RAG & Retrieval Engine."""

import math
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from madhav.rag.domain.exceptions import EmbeddingDimensionMismatchError, EmbeddingProviderError


class EmbeddingModelInfo(BaseModel):
    """Metadata describing the embedding model configuration."""

    provider: str = Field(description="Embedding provider identifier (e.g. 'development')")
    model_name: str = Field(description="Embedding model name (e.g. 'dev-hash-embed-v1')")
    dimensions: int = Field(description="Vector embedding output dimensions")
    version: str = Field(default="1.0", description="Model version string")


class EmbeddingVector(BaseModel):
    """Domain model representing a chunk's dense vector embedding."""

    embedding_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Embedding unique identifier"
    )
    chunk_id: str = Field(description="Associated chunk identifier")
    document_id: str = Field(description="Associated document identifier")
    owner_id: str = Field(description="Owner user identifier")
    model_info: EmbeddingModelInfo = Field(description="Embedding model provenance metadata")
    vector: list[float] = Field(description="Dense floating point vector values")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Embedding creation timestamp"
    )

    @model_validator(mode="after")
    def validate_vector_integrity(self) -> "EmbeddingVector":
        """Validate vector values for non-emptiness, finiteness, and dimension match."""
        if not self.vector:
            raise EmbeddingProviderError("Embedding vector cannot be empty.")

        expected_dims = self.model_info.dimensions
        actual_dims = len(self.vector)
        if actual_dims != expected_dims:
            raise EmbeddingDimensionMismatchError(expected=expected_dims, actual=actual_dims)

        for val in self.vector:
            if math.isnan(val) or math.isinf(val):
                raise EmbeddingProviderError(
                    "Embedding vector contains invalid non-finite value (NaN or Infinity)."
                )

        return self
