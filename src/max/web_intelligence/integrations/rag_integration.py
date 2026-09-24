"""RAG integration converting Web Intelligence research evidence into RAG-ready document chunks."""

from typing import Any

from max.web_intelligence.domain.models import ResearchResult


class WebRAGIntegrationAdapter:
    """Converts web evidence and research results into Module 10 RAG indexable payload formats."""

    @staticmethod
    def prepare_rag_chunks(result: ResearchResult) -> list[dict[str, Any]]:
        """Extract structured document chunks for optional RAG indexing."""
        chunks: list[dict[str, Any]] = []

        for ev in result.evidence:
            chunk = {
                "chunk_id": f"rag_{ev.id}",
                "text": f"Claim: {ev.claim}\nSource: {ev.source_title} ({ev.source_url})",
                "metadata": {
                    "research_id": result.research_id,
                    "source_url": ev.source_url,
                    "source_title": ev.source_title,
                    "confidence": ev.confidence.value,
                    "evidence_type": ev.evidence_type.value,
                    "published_date": ev.published_date,
                },
            }
            chunks.append(chunk)

        return chunks
