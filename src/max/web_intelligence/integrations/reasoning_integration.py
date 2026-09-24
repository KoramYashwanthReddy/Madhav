"""Reasoning integration adapting web research evidence for Module 11 Reasoning Engine."""

from typing import Any

from max.web_intelligence.domain.models import ResearchResult


class WebReasoningIntegrationAdapter:
    """Adapts Web Intelligence evidence and conflict structures for Module 11 Reasoning Engine input."""

    @staticmethod
    def prepare_reasoning_facts(result: ResearchResult) -> dict[str, Any]:
        """Format evidence and conflicts into structured premises for reasoning."""
        premises: list[dict[str, Any]] = []
        for ev in result.evidence:
            premises.append(
                {
                    "premise_id": ev.id,
                    "statement": ev.claim,
                    "source": ev.source_title,
                    "confidence": ev.confidence.value,
                }
            )

        conflicts: list[dict[str, Any]] = []
        for c in result.synthesis.conflicts:
            conflicts.append(
                {
                    "conflict_id": c.id,
                    "type": c.conflict_type.value,
                    "claim_summary": c.claim_summary,
                    "evidence_a_id": c.evidence_a.id,
                    "evidence_b_id": c.evidence_b.id,
                }
            )

        return {
            "research_id": result.research_id,
            "topic": result.objective.topic,
            "question": result.objective.question,
            "premises": premises,
            "conflicts": conflicts,
        }
