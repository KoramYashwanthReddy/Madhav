"""EvidenceService for extracting claims, quotes, and provenance-linked evidence."""

import re

from max.web_intelligence.domain.enums import EvidenceConfidence, EvidenceType
from max.web_intelligence.domain.models import (
    Evidence,
    EvidenceQuoteReference,
    ResearchRequest,
    Source,
    WebDocument,
)


class EvidenceService:
    """Extracts factual claims and links evidence items back to source documents."""

    def extract_evidence(
        self, request: ResearchRequest, source: Source, document: WebDocument
    ) -> list[Evidence]:
        """Extract factual evidence items from document text."""
        evidence_items: list[Evidence] = []
        text = document.content.raw_text

        # Split text into candidate sentence chunks
        [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 15]

        topic_terms = [t.lower() for t in request.objective.topic.split() if len(t) > 2]

        for sec_idx, sec in enumerate(document.content.sections):
            sec_text = sec.text
            sec_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", sec_text) if len(s.strip()) > 15]

            for s_idx, sentence in enumerate(sec_sentences):
                s_lower = sentence.lower()
                # Check relevance to topic or question keywords
                is_relevant = any(term in s_lower for term in topic_terms) or (s_idx == 0 and sec_idx == 0)

                if is_relevant:
                    ev_type = EvidenceType.DIRECT_FACT
                    if any(char.isdigit() for char in sentence):
                        ev_type = EvidenceType.STATISTICAL_DATA

                    conf = EvidenceConfidence.MEDIUM
                    if source.trust.is_primary or source.trust.is_official:
                        conf = EvidenceConfidence.HIGH

                    quote_ref = EvidenceQuoteReference(
                        exact_quote=sentence[:300],
                        section_index=sec.section_index,
                        char_offset=sec_text.find(sentence) if sentence in sec_text else 0,
                    )

                    ev = Evidence(
                        research_id=request.id,
                        source_id=source.id,
                        document_id=document.id,
                        claim=sentence,
                        evidence_type=ev_type,
                        quote_ref=quote_ref,
                        confidence=conf,
                        source_url=source.metadata.url,
                        source_title=source.metadata.title,
                        published_date=source.metadata.published_date,
                    )

                    evidence_items.append(ev)

                    if len(evidence_items) >= 10:
                        break

        # Fallback evidence if none extracted
        if not evidence_items:
            summary_claim = f"{source.metadata.title}: Information regarding {request.objective.topic} retrieved from {source.metadata.domain}."
            evidence_items.append(
                Evidence(
                    research_id=request.id,
                    source_id=source.id,
                    document_id=document.id,
                    claim=summary_claim,
                    evidence_type=EvidenceType.STATEMENT,
                    confidence=EvidenceConfidence.MEDIUM,
                    source_url=source.metadata.url,
                    source_title=source.metadata.title,
                    published_date=source.metadata.published_date,
                )
            )

        return evidence_items
