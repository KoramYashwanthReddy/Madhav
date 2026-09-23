"""Retrieval Service for RAG & Retrieval Engine."""

import logging
import time
from typing import Any

from max.rag.domain.query import RetrievalQuery
from max.rag.domain.result import Citation, RetrievalResponse, RetrievalResult
from max.rag.providers.base import EmbeddingProvider
from max.rag.services.normalizer import TextNormalizer
from max.rag.stores.base import VectorStore

logger = logging.getLogger(__name__)


class RetrievalService:
    """Core retrieval engine orchestrating vector search, filtering, ranking, and citations."""

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        default_top_k: int = 5,
        max_top_k: int = 50,
        default_minimum_score: float = 0.0,
    ) -> None:
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.default_top_k = default_top_k
        self.max_top_k = max_top_k
        self.default_minimum_score = default_minimum_score

    async def retrieve(self, query: RetrievalQuery) -> RetrievalResponse:
        """Execute a retrieval query against the vector store.

        Privacy guarantee: Full query text or content is never logged in production.
        Only metadata metrics (result count, provider, duration_ms, owner_id) are logged.
        """
        start_time = time.perf_counter()

        # 1. Normalize query text
        normalized_query_text = TextNormalizer.normalize(query.query_text)

        # 2. Adjust top_k and minimum_score within bounds
        effective_top_k = min(query.top_k, self.max_top_k)
        effective_score = (
            query.minimum_score
            if query.minimum_score > 0.0
            else self.default_minimum_score
        )

        adjusted_query = RetrievalQuery(
            query_text=normalized_query_text,
            owner_id=query.owner_id,
            top_k=effective_top_k,
            minimum_score=effective_score,
            filters=query.filters,
            source_types=query.source_types,
            document_types=query.document_types,
            include_archived=query.include_archived,
            include_deleted=query.include_deleted,
        )

        # 3. Generate query vector embedding
        query_vector = await self.embedding_provider.embed_text(normalized_query_text)

        # 4. Perform vector similarity search
        raw_results: list[RetrievalResult] = await self.vector_store.similarity_search(
            query_vector=query_vector, query=adjusted_query
        )

        # 5. Extract citations
        citations: list[Citation] = [res.citation for res in raw_results]

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Privacy-safe log statement
        logger.info(
            "RAG search executed for owner %s: provider=%s, results=%d, duration_ms=%.2f",
            query.owner_id,
            self.embedding_provider.model_info().provider,
            len(raw_results),
            elapsed_ms,
        )

        metadata: dict[str, str | int | float | bool | list[str]] = {
            "embedding_provider": self.embedding_provider.model_info().provider,
            "embedding_model": self.embedding_provider.model_info().model_name,
            "vector_dimensions": self.embedding_provider.model_info().dimensions,
            "total_results": len(raw_results),
        }

        return RetrievalResponse(
            query=adjusted_query,
            results=raw_results,
            total_retrieved=len(raw_results),
            citations=citations,
            execution_time_ms=elapsed_ms,
            metadata=metadata,
        )

    async def get_status(self) -> dict[str, Any]:
        """Return diagnostic subsystem status."""
        store_health = await self.vector_store.health()
        model_info = self.embedding_provider.model_info()

        return {
            "rag_enabled": True,
            "embedding_provider": model_info.provider,
            "embedding_model": model_info.model_name,
            "embedding_dimensions": model_info.dimensions,
            "vector_store_provider": store_health.get("provider", "unknown"),
            "vector_store_health": store_health,
            "default_top_k": self.default_top_k,
            "max_top_k": self.max_top_k,
            "default_minimum_score": self.default_minimum_score,
        }
