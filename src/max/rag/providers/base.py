"""Abstract Embedding Provider interface for RAG & Retrieval Engine."""

from abc import ABC, abstractmethod
from typing import Any

from max.rag.domain.embedding import EmbeddingModelInfo


class EmbeddingProvider(ABC):
    """Abstract interface defining the contract for embedding providers."""

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        """Generate a dense float vector embedding for a single text payload."""

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate dense vector embeddings for a batch of text payloads."""

    @abstractmethod
    def capabilities(self) -> dict[str, Any]:
        """Return provider capabilities (batch size, max tokens, etc.)."""

    @abstractmethod
    def model_info(self) -> EmbeddingModelInfo:
        """Return embedding model metadata information."""
