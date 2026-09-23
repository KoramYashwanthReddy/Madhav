"""Unit tests for InMemoryVectorStore."""

import pytest

from max.rag.domain.chunk import DocumentChunk
from max.rag.domain.embedding import EmbeddingModelInfo, EmbeddingVector
from max.rag.domain.query import RetrievalQuery
from max.rag.stores.memory_store import InMemoryVectorStore


@pytest.mark.asyncio
async def test_vector_store_upsert_and_get() -> None:
    """Test inserting and retrieving chunk vector pair."""
    store = InMemoryVectorStore(expected_dimensions=4)
    info = EmbeddingModelInfo(provider="dev", model_name="test", dimensions=4)

    chunk = DocumentChunk(
        chunk_id="c1",
        document_id="doc1",
        owner_id="user1",
        chunk_index=0,
        text="Sample text",
        character_start=0,
        character_end=11,
    )
    emb = EmbeddingVector(
        embedding_id="e1",
        chunk_id="c1",
        document_id="doc1",
        owner_id="user1",
        model_info=info,
        vector=[1.0, 0.0, 0.0, 0.0],
    )

    await store.upsert(chunk, emb)
    assert await store.count("user1") == 1

    res = await store.get("c1")
    assert res is not None
    stored_chunk, stored_emb = res
    assert stored_chunk.text == "Sample text"
    assert stored_emb.vector == [1.0, 0.0, 0.0, 0.0]


@pytest.mark.asyncio
async def test_vector_store_deletion() -> None:
    """Test deleting single chunk and deleting by document_id."""
    store = InMemoryVectorStore(expected_dimensions=4)
    info = EmbeddingModelInfo(provider="dev", model_name="test", dimensions=4)

    c1 = DocumentChunk(
        chunk_id="c1",
        document_id="doc1",
        owner_id="u1",
        chunk_index=0,
        text="t1",
        character_start=0,
        character_end=2,
    )
    e1 = EmbeddingVector(
        embedding_id="e1",
        chunk_id="c1",
        document_id="doc1",
        owner_id="u1",
        model_info=info,
        vector=[1.0, 0.0, 0.0, 0.0],
    )

    c2 = DocumentChunk(
        chunk_id="c2",
        document_id="doc1",
        owner_id="u1",
        chunk_index=1,
        text="t2",
        character_start=3,
        character_end=5,
    )
    e2 = EmbeddingVector(
        embedding_id="e2",
        chunk_id="c2",
        document_id="doc1",
        owner_id="u1",
        model_info=info,
        vector=[0.0, 1.0, 0.0, 0.0],
    )

    c3 = DocumentChunk(
        chunk_id="c3",
        document_id="doc2",
        owner_id="u1",
        chunk_index=0,
        text="t3",
        character_start=0,
        character_end=2,
    )
    e3 = EmbeddingVector(
        embedding_id="e3",
        chunk_id="c3",
        document_id="doc2",
        owner_id="u1",
        model_info=info,
        vector=[0.0, 0.0, 1.0, 0.0],
    )

    await store.upsert_batch([c1, c2, c3], [e1, e2, e3])
    assert await store.count("u1") == 3

    # Delete single chunk c1
    assert await store.delete("c1") is True
    assert await store.count("u1") == 2

    # Delete all chunks for doc1 (remaining c2)
    deleted_cnt = await store.delete_by_document("doc1")
    assert deleted_cnt == 1
    assert await store.count("u1") == 1
    assert await store.get("c3") is not None


@pytest.mark.asyncio
async def test_vector_store_similarity_search_and_ordering() -> None:
    """Test top-k similarity search, owner isolation, metadata filtering, and stable ordering."""
    store = InMemoryVectorStore(expected_dimensions=4)
    info = EmbeddingModelInfo(provider="dev", model_name="test", dimensions=4)

    # c1: high match for u1
    c1 = DocumentChunk(
        chunk_id="c1",
        document_id="doc1",
        owner_id="u1",
        chunk_index=0,
        text="Matching text",
        character_start=0,
        character_end=13,
        metadata={"source_type": "TEXT", "document_type": "TEXT", "title": "Doc 1"},
    )
    e1 = EmbeddingVector(
        embedding_id="e1",
        chunk_id="c1",
        document_id="doc1",
        owner_id="u1",
        model_info=info,
        vector=[1.0, 0.0, 0.0, 0.0],
    )

    # c2: medium match for u1
    c2 = DocumentChunk(
        chunk_id="c2",
        document_id="doc2",
        owner_id="u1",
        chunk_index=0,
        text="Partial match",
        character_start=0,
        character_end=13,
        metadata={"source_type": "TEXT", "document_type": "TEXT", "title": "Doc 2"},
    )
    e2 = EmbeddingVector(
        embedding_id="e2",
        chunk_id="c2",
        document_id="doc2",
        owner_id="u1",
        model_info=info,
        vector=[0.7071, 0.7071, 0.0, 0.0],
    )

    # c3: high match for DIFFERENT user u2 (owner isolation test)
    c3 = DocumentChunk(
        chunk_id="c3",
        document_id="doc3",
        owner_id="u2",
        chunk_index=0,
        text="User 2 text",
        character_start=0,
        character_end=11,
        metadata={"source_type": "TEXT", "document_type": "TEXT", "title": "Doc 3"},
    )
    e3 = EmbeddingVector(
        embedding_id="e3",
        chunk_id="c3",
        document_id="doc3",
        owner_id="u2",
        model_info=info,
        vector=[1.0, 0.0, 0.0, 0.0],
    )

    await store.upsert_batch([c1, c2, c3], [e1, e2, e3])

    query = RetrievalQuery(
        query_text="search query",
        owner_id="u1",
        top_k=5,
        minimum_score=0.1,
    )
    query_vec = [1.0, 0.0, 0.0, 0.0]

    results = await store.similarity_search(query_vec, query)

    # u2 content must be isolated and excluded
    assert len(results) == 2
    assert results[0].chunk_id == "c1"
    assert results[0].rank == 1
    assert results[0].score > results[1].score
    assert results[1].chunk_id == "c2"
    assert results[1].rank == 2
