"""SynthesisService for compiling evidence, findings, citations, and summaries."""

from max.web_intelligence.domain.models import (
    Citation,
    Evidence,
    EvidenceConflict,
    ResearchFinding,
    ResearchQualityReport,
    ResearchRequest,
    ResearchSummary,
    ResearchSynthesis,
    Source,
)


class ResearchSynthesisService:
    """Synthesizes structured evidence and citations into ResearchSynthesis output."""

    def synthesize(
        self,
        request: ResearchRequest,
        sources: list[Source],
        evidence_list: list[Evidence],
        citations: list[Citation],
        conflicts: list[EvidenceConflict],
        quality_report: ResearchQualityReport,
    ) -> ResearchSynthesis:
        """Compile research findings and citations into ResearchSynthesis."""
        findings: list[ResearchFinding] = []
        cit_map = {c.source_id: c.id for c in citations}

        # Create findings from evidence
        for ev in evidence_list[:10]:
            matching_cit_id = cit_map.get(ev.source_id)
            finding = ResearchFinding(
                statement=ev.claim,
                supporting_evidence_ids=[ev.id],
                citation_ids=[matching_cit_id] if matching_cit_id else [],
                confidence=ev.confidence,
            )
            findings.append(finding)

        overview_text = (
            f"Research summary for objective '{request.objective.topic}': "
            f"Evaluated {len(sources)} sources across {len({s.metadata.domain for s in sources})} domains. "
            f"Extracted {len(evidence_list)} evidence claims with {len(citations)} validated citations."
        )

        key_points = [ev.claim for ev in evidence_list[:5]]

        limitations: list[str] = []
        uncertainties: list[str] = []

        if conflicts:
            limitations.append(f"Identified {len(conflicts)} conflict(s) across retrieved sources.")
            for c in conflicts:
                uncertainties.append(c.claim_summary)

        if not sources:
            limitations.append("No relevant candidate sources were discovered.")

        summary = ResearchSummary(
            overview=overview_text,
            key_points=key_points,
            limitations=limitations,
            uncertainties=uncertainties,
        )

        return ResearchSynthesis(
            summary=summary,
            findings=findings,
            citations=citations,
            conflicts=conflicts,
            quality_report=quality_report,
        )
