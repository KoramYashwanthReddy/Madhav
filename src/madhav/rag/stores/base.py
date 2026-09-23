"""Abstract Vector Store interface for RAG & Retrieval Engine."""

from abc import ABC, abstractmethod
from typing import Any

from madhav.rag.domain.chunk import DocumentChunk
from madhav.rag.domain.embedding import EmbeddingVector
from madhav.rag.domain.query import RetrievalQuery
from madhav.rag.domain.result import RetrievalResult


class VectorStore(ABC):
    """Abstract interface defining operations for vector storage and retrieval."""

    @abstractmethod
    async def upsert(self, chunk: DocumentChunk, embedding: EmbeddingVector) -> None:
        """Insert or update a chunk vector record."""

    @abstractmethod
    async def upsert_batch(
        self, chunks: list[DocumentChunk], embeddings: list[EmbeddingVector]
    ) -> None:
        """Batch insert or update chunk vector records."""

    @abstractmethod
    async def delete(self, chunk_id: str) -> bool:
        """Delete a single chunk vector record by chunk_id."""

    @abstractmethod
    async def delete_by_document(self, document_id: str) -> int:
        """Delete all chunk vector records associated with document_id."""

    @abstractmethod
    async def get(self, chunk_id: str) -> tuple[DocumentChunk, EmbeddingVector] | None:
        """Retrieve a stored chunk and embedding pair by chunk_id."""

    @abstractmethod
    async def similarity_search(
        self, query_vector: list[float], query: RetrievalQuery
    ) -> list[RetrievalResult]:
        """Perform vector similarity search with metadata filtering and deterministic ordering."""

    @abstractmethod
    async def count(self, owner_id: str | None = None) -> int:
        """Return total stored vector count, optionally filtered by owner_id."""

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        """Return health and status diagnostic metrics."""
