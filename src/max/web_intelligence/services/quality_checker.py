"""QualityChecker service for calculating ResearchQualityReport metrics."""

from max.web_intelligence.domain.models import (
    Citation,
    EvidenceConflict,
    ResearchQualityReport,
    ResearchRequest,
    Source,
)


class ResearchQualityChecker:
    """Evaluates the structural quality and completeness of research findings."""

    def evaluate_quality(
        self,
        request: ResearchRequest,
        sources: list[Source],
        citations: list[Citation],
        conflicts: list[EvidenceConflict],
    ) -> ResearchQualityReport:
        """Calculate quality score and compliance notes."""
        domains = {s.metadata.domain for s in sources}
        notes: list[str] = []

        score = 1.0
        if not sources:
            score -= 0.5
            notes.append("No sources discovered.")
        elif len(domains) < 2:
            score -= 0.15
            notes.append("Low source domain diversity (less than 2 distinct domains).")

        if not citations:
            score -= 0.2
            notes.append("No citations produced.")

        if conflicts:
            notes.append(f"{len(conflicts)} conflict(s) detected between sources.")

        score = max(0.0, min(1.0, round(score, 2)))

        return ResearchQualityReport(
            objective_answered=len(sources) > 0,
            sources_count=len(sources),
            distinct_domains_count=len(domains),
            conflicts_count=len(conflicts),
            citations_count=len(citations),
            freshness_satisfied=True,
            quality_score=score,
            notes=notes,
        )
