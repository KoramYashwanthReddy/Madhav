"""Deterministic in-memory vector store for testing and development."""

from typing import Any

from madhav.rag.domain.chunk import DocumentChunk
from madhav.rag.domain.document import DocumentSource
from madhav.rag.domain.embedding import EmbeddingVector
from madhav.rag.domain.enums import DocumentSourceType, DocumentStatus, DocumentType
from madhav.rag.domain.exceptions import EmbeddingDimensionMismatchError
from madhav.rag.domain.query import RetrievalQuery
from madhav.rag.domain.result import Citation, RetrievalResult
from madhav.rag.services.similarity import cosine_similarity
from madhav.rag.stores.base import VectorStore


class InMemoryVectorStore(VectorStore):
    """In-memory vector store implementing deterministic top-k cosine similarity retrieval."""

    def __init__(self, expected_dimensions: int = 64) -> None:
        self._expected_dimensions = expected_dimensions
        # Store records as chunk_id -> (DocumentChunk, EmbeddingVector)
        self._store: dict[str, tuple[DocumentChunk, EmbeddingVector]] = {}

    async def upsert(self, chunk: DocumentChunk, embedding: EmbeddingVector) -> None:
        """Insert or replace chunk vector pair."""
        if len(embedding.vector) != self._expected_dimensions:
            raise EmbeddingDimensionMismatchError(
                expected=self._expected_dimensions, actual=len(embedding.vector)
            )
        self._store[chunk.chunk_id] = (chunk, embedding)

    async def upsert_batch(
        self, chunks: list[DocumentChunk], embeddings: list[EmbeddingVector]
    ) -> None:
        """Batch insert chunk vector pairs."""
        for chunk, emb in zip(chunks, embeddings, strict=True):
            await self.upsert(chunk, emb)

    async def delete(self, chunk_id: str) -> bool:
        """Delete chunk record by ID."""
        if chunk_id in self._store:
            del self._store[chunk_id]
            return True
        return False

    async def delete_by_document(self, document_id: str) -> int:
        """Delete all chunk records matching document_id."""
        to_delete = [
            cid for cid, (chunk, _) in self._store.items() if chunk.document_id == document_id
        ]
        for cid in to_delete:
            del self._store[cid]
        return len(to_delete)

    async def get(self, chunk_id: str) -> tuple[DocumentChunk, EmbeddingVector] | None:
        """Get chunk and embedding by chunk_id."""
        return self._store.get(chunk_id)

    async def similarity_search(
        self, query_vector: list[float], query: RetrievalQuery
    ) -> list[RetrievalResult]:
        """Perform deterministic cosine similarity search with filters."""
        if len(query_vector) != self._expected_dimensions:
            raise EmbeddingDimensionMismatchError(
                expected=self._expected_dimensions, actual=len(query_vector)
            )

        candidates: list[tuple[float, str, DocumentChunk, EmbeddingVector]] = []

        for cid, (chunk, emb) in self._store.items():
            # 1. Owner isolation filter
            if chunk.owner_id != query.owner_id:
                continue

            # 2. Metadata filtering
            if not self._matches_filters(chunk, query):
                continue

            # 3. Calculate cosine similarity
            score = cosine_similarity(query_vector, emb.vector)

            # 4. Minimum score threshold filter
            if score < query.minimum_score:
                continue

            candidates.append((score, cid, chunk, emb))

        # 5. Deterministic sorting: score DESCENDING, chunk_id ASCENDING (for stable tie-breaking)
        candidates.sort(key=lambda item: (-item[0], item[1]))

        # 6. Apply top_k truncation
        top_matches = candidates[: query.top_k]

        # 7. Construct domain RetrievalResult objects
        results: list[RetrievalResult] = []
        for rank, (score, _cid, chunk, _emb) in enumerate(top_matches, start=1):
            src_type_str = str(chunk.metadata.get("source_type", DocumentSourceType.TEXT))
            try:
                src_type = DocumentSourceType(src_type_str)
            except ValueError:
                src_type = DocumentSourceType.TEXT

            src_ref = str(chunk.metadata.get("source_reference", chunk.document_id))
            doc_title = str(chunk.metadata.get("title", f"Document {chunk.document_id[:8]}"))

            uri_val = chunk.metadata.get("uri")
            uri_str = uri_val if isinstance(uri_val, str) else None

            source = DocumentSource(
                source_type=src_type,
                source_reference=src_ref,
                uri=uri_str,
            )

            location_lbl = (
                f"Paragraph {chunk.metadata.get('paragraph_index', chunk.chunk_index)}"
            )

            citation = Citation(
                document_id=chunk.document_id,
                chunk_id=chunk.chunk_id,
                source_type=src_type,
                source_reference=src_ref,
                title=doc_title,
                location=location_lbl,
                score=score,
            )

            result = RetrievalResult(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                text=chunk.text,
                score=score,
                rank=rank,
                metadata=chunk.metadata,
                source=source,
                citation=citation,
            )
            results.append(result)

        return results

    async def count(self, owner_id: str | None = None) -> int:
        """Count total stored records."""
        if owner_id is None:
            return len(self._store)
        return sum(1 for chunk, _ in self._store.values() if chunk.owner_id == owner_id)

    async def health(self) -> dict[str, Any]:
        """Return diagnostic health metrics."""
        return {
            "provider": "memory",
            "status": "healthy",
            "dimensions": self._expected_dimensions,
            "total_chunks": len(self._store),
        }

    def _matches_filters(self, chunk: DocumentChunk, query: RetrievalQuery) -> bool:
        """Evaluate chunk against query filters and document state."""
        meta = chunk.metadata

        # Document Status filter
        doc_status = str(meta.get("status", DocumentStatus.INDEXED))
        if doc_status == DocumentStatus.DELETED and not query.include_deleted:
            return False
        if doc_status == DocumentStatus.ARCHIVED and not query.include_archived:
            return False

        # Filter by document_types
        allowed_doc_types = query.document_types or query.filters.document_type
        if allowed_doc_types is not None:
            doc_list = (
                allowed_doc_types
                if isinstance(allowed_doc_types, list)
                else [allowed_doc_types]
            )
            allowed_doc_set = {str(t) for t in doc_list}
            chunk_doc_type = str(meta.get("document_type", DocumentType.TEXT))
            if chunk_doc_type not in allowed_doc_set:
                return False

        # Filter by source_types
        allowed_src_types = query.source_types or query.filters.source_type
        if allowed_src_types is not None:
            src_list = (
                allowed_src_types
                if isinstance(allowed_src_types, list)
                else [allowed_src_types]
            )
            allowed_src_set = {str(s) for s in src_list}
            chunk_src_type = str(meta.get("source_type", DocumentSourceType.TEXT))
            if chunk_src_type not in allowed_src_set:
                return False

        # Filter by document_id
        if query.filters.document_id:
            target_ids = query.filters.document_id
            if isinstance(target_ids, str):
                target_ids = [target_ids]
            if chunk.document_id not in target_ids:
                return False

        # Filter by collection_id
        if query.filters.collection_id:
            chunk_coll = meta.get("collection_id")
            if chunk_coll != query.filters.collection_id:
                return False

        # Filter by tags
        if query.filters.tags:
            chunk_tags = meta.get("tags")
            if not isinstance(chunk_tags, list):
                return False
            if not any(t in chunk_tags for t in query.filters.tags):
                return False

        return True
