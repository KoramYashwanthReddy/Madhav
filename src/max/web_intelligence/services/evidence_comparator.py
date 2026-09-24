"""EvidenceComparator service for cross-source comparison and conflict detection."""

import re

from max.web_intelligence.domain.enums import ConflictType
from max.web_intelligence.domain.models import Evidence, EvidenceConflict, Source


class EvidenceComparator:
    """Compares evidence across distinct web sources to identify agreement or conflicts."""

    def compare_evidence(
        self, research_id: str, evidence_list: list[Evidence], sources: list[Source]
    ) -> list[EvidenceConflict]:
        """Detect conflicts or discrepancies across extracted evidence items."""
        conflicts: list[EvidenceConflict] = []
        source_map = {s.id: s for s in sources}

        # Pairwise check for date or factual contradictions
        for i in range(len(evidence_list)):
            for j in range(i + 1, len(evidence_list)):
                ev_a = evidence_list[i]
                ev_b = evidence_list[j]

                # Only compare evidence from different sources
                if ev_a.source_id == ev_b.source_id:
                    continue

                # Date mismatch check
                if ev_a.published_date and ev_b.published_date and ev_a.published_date != ev_b.published_date:
                    # Check if claims discuss the same date/version event
                    if self._is_similar_claim(ev_a.claim, ev_b.claim):
                        conflicts.append(
                            EvidenceConflict(
                                research_id=research_id,
                                conflict_type=ConflictType.DATE_MISMATCH,
                                claim_summary=f"Publication date difference between '{ev_a.source_title}' ({ev_a.published_date}) and '{ev_b.source_title}' ({ev_b.published_date})",
                                evidence_a=ev_a,
                                evidence_b=ev_b,
                                notes="Publication or event release dates differ between sources.",
                            )
                        )

                # Direct negation or contradictory numerical claim check
                elif self._is_contradictory(ev_a.claim, ev_b.claim):
                    conflicts.append(
                        EvidenceConflict(
                            research_id=research_id,
                            conflict_type=ConflictType.CLAIM_CONTRADICTION,
                            claim_summary=f"Contradictory claim regarding '{ev_a.claim[:60]}...'",
                            evidence_a=ev_a,
                            evidence_b=ev_b,
                            notes="Direct contradiction detected between retrieved sources.",
                        )
                    )

        return conflicts

    def _is_similar_claim(self, claim_a: str, claim_b: str) -> bool:
        """Check if two claims refer to similar concepts."""
        words_a = set(re.findall(r"\w+", claim_a.lower()))
        words_b = set(re.findall(r"\w+", claim_b.lower()))
        intersection = words_a.intersection(words_b)
        union = words_a.union(words_b)
        return len(intersection) / max(len(union), 1) > 0.3

    def _is_contradictory(self, claim_a: str, claim_b: str) -> bool:
        """Detect explicit contradiction markers (e.g. not, failed vs succeeded)."""
        ca = claim_a.lower()
        cb = claim_b.lower()

        # Check for inverse polarity
        negations = ["not", "failed", "denied", "rejected", "false", "deprecated"]
        positives = ["released", "success", "approved", "true", "active", "supported"]

        has_neg_a = any(n in ca for n in negations)
        has_pos_a = any(p in ca for p in positives)

        has_neg_b = any(n in cb for n in negations)
        has_pos_b = any(p in cb for p in positives)

        if (has_neg_a and has_pos_b and self._is_similar_claim(claim_a, claim_b)) or (
            has_pos_a and has_neg_b and self._is_similar_claim(claim_a, claim_b)
        ):
            return True
        return False
