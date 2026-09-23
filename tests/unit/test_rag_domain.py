"""Unit tests for RAG Domain Models."""

import pytest

from max.rag.domain.document import Document, DocumentSource
from max.rag.domain.embedding import EmbeddingModelInfo, EmbeddingVector
from max.rag.domain.enums import DocumentSourceType, DocumentStatus
from max.rag.domain.exceptions import (
    DocumentValidationError,
    EmbeddingDimensionMismatchError,
    EmbeddingProviderError,
    RetrievalValidationError,
)
from max.rag.domain.query import RetrievalQuery
from max.rag.domain.result import Citation, RetrievalResult


def test_document_lifecycle_transitions() -> None:
    """Test valid and invalid document lifecycle status transitions."""
    source = DocumentSource(
        source_type=DocumentSourceType.TEXT,
        source_reference="ref-123",
    )
    doc = Document(
        owner_id="user-1",
        title="Test Doc",
        content="Hello world",
        source=source,
        content_hash="abc123hash",
    )

    assert doc.status == DocumentStatus.ACTIVE

    # Valid transition ACTIVE -> INDEXING
    doc.transition_to(DocumentStatus.INDEXING)
    assert doc.status == DocumentStatus.INDEXING

    # Valid transition INDEXING -> INDEXED
    doc.transition_to(DocumentStatus.INDEXED)
    assert doc.status == DocumentStatus.INDEXED
    assert doc.indexed_at is not None

    # Invalid transition INDEXED -> ACTIVE (must raise DocumentValidationError)
    with pytest.raises(DocumentValidationError):
        doc.transition_to(DocumentStatus.ACTIVE)


def test_embedding_vector_validation() -> None:
    """Test embedding vector dimension and value integrity checks."""
    info = EmbeddingModelInfo(
        provider="dev",
        model_name="dev-hash-embed-v1",
        dimensions=4,
    )

    # Valid vector
    emb = EmbeddingVector(
        chunk_id="chunk-1",
        document_id="doc-1",
        owner_id="user-1",
        model_info=info,
        vector=[0.1, 0.2, 0.3, 0.4],
    )
    assert len(emb.vector) == 4

    # Dimension mismatch
    with pytest.raises(EmbeddingDimensionMismatchError):
        EmbeddingVector(
            chunk_id="chunk-1",
            document_id="doc-1",
            owner_id="user-1",
            model_info=info,
            vector=[0.1, 0.2],
        )

    # Non-finite values (NaN / Inf)
    with pytest.raises(EmbeddingProviderError):
        EmbeddingVector(
            chunk_id="chunk-1",
            document_id="doc-1",
            owner_id="user-1",
            model_info=info,
            vector=[0.1, float("nan"), 0.3, 0.4],
        )


def test_retrieval_query_validation() -> None:
    """Test validation of RetrievalQuery inputs."""
    # Empty query string
    with pytest.raises(RetrievalValidationError):
        RetrievalQuery(query_text="   ", owner_id="user-1")

    # Invalid top_k <= 0
    with pytest.raises(RetrievalValidationError):
        RetrievalQuery(query_text="valid query", owner_id="user-1", top_k=0)

    # Invalid minimum_score out of range
    with pytest.raises(RetrievalValidationError):
        RetrievalQuery(query_text="valid query", owner_id="user-1", minimum_score=1.5)


def test_citation_and_result_structures() -> None:
    """Test citation and retrieval result models."""
    source = DocumentSource(
        source_type=DocumentSourceType.FILE,
        source_reference="file.txt",
    )
    citation = Citation(
        document_id="doc-1",
        chunk_id="chunk-1",
        source_type=DocumentSourceType.FILE,
        source_reference="file.txt",
        title="Test File",
        location="Paragraph 1",
        score=0.92,
    )
    res = RetrievalResult(
        chunk_id="chunk-1",
        document_id="doc-1",
        text="Sample text content",
        score=0.92,
        rank=1,
        metadata={"key": "val"},
        source=source,
        citation=citation,
    )
    assert res.score == 0.92
    assert res.citation.title == "Test File"
