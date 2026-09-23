"""Retrieval Result domain model for RAG & Retrieval Engine."""

from pydantic import BaseModel, Field

from madhav.rag.domain.document import DocumentSource
from madhav.rag.domain.enums import DocumentSourceType
from madhav.rag.domain.query import RetrievalQuery


class Citation(BaseModel):
    """Provenance citation structure for a retrieved chunk."""

    document_id: str = Field(description="Parent Document identifier")
    chunk_id: str = Field(description="Retrieved chunk identifier")
    source_type: DocumentSourceType = Field(description="Provenance source category")
    source_reference: str = Field(description="Original source reference key")
    title: str = Field(description="Source document title")
    location: str | None = Field(default=None, description="Optional chunk location label")
    score: float = Field(description="Similarity relevance score")


class RetrievalResult(BaseModel):
    """Domain model representing a single ranked retrieval match."""

    chunk_id: str = Field(description="Matching chunk identifier")
    document_id: str = Field(description="Parent document identifier")
    text: str = Field(description="Matched text payload content")
    score: float = Field(description="Vector similarity score (0.0 to 1.0)")
    rank: int = Field(description="1-based rank position in result set")
    metadata: dict[str, str | int | float | bool | list[str]] = Field(
        default_factory=dict, description="Metadata key-value pairs"
    )
    source: DocumentSource = Field(description="Document source provenance information")
    citation: Citation = Field(description="Structured citation metadata")


class RetrievalResponse(BaseModel):
    """Domain model representing complete retrieval search response."""

    query: RetrievalQuery = Field(description="Copy of executed retrieval query")
    results: list[RetrievalResult] = Field(description="Ranked list of matching retrieval results")
    total_retrieved: int = Field(description="Total count of matching items returned")
    citations: list[Citation] = Field(description="Convenience list of all result citations")
    execution_time_ms: float = Field(description="Total retrieval search latency in milliseconds")
    metadata: dict[str, str | int | float | bool | list[str]] = Field(
        default_factory=dict, description="Execution diagnostic metadata"
    )
