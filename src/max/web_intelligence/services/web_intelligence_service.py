"""Master WebIntelligenceService orchestrating the 10-stage research pipeline."""

import logging
from datetime import UTC, datetime

from max.config.sections import WebIntelligenceSettings
from max.web_intelligence.domain.enums import ResearchStatus
from max.web_intelligence.domain.exceptions import (
    ResearchCancelledError,
    ResearchNotFoundError,
)
from max.web_intelligence.domain.models import (
    Citation,
    Evidence,
    EvidenceConflict,
    ResearchRequest,
    ResearchResult,
)
from max.web_intelligence.providers.base import BaseSearchProvider
from max.web_intelligence.providers.mock import MockSearchProvider
from max.web_intelligence.repositories.repositories import (
    EvidenceRepository,
    ResearchAuditRepository,
    ResearchRepository,
    SourceRepository,
)
from max.web_intelligence.services.audit_service import ResearchAuditService
from max.web_intelligence.services.citation_service import CitationService
from max.web_intelligence.services.content_acquisition import ContentAcquisitionService
from max.web_intelligence.services.content_extraction import ContentExtractionService
from max.web_intelligence.services.evidence_comparator import EvidenceComparator
from max.web_intelligence.services.evidence_service import EvidenceService
from max.web_intelligence.services.quality_checker import ResearchQualityChecker
from max.web_intelligence.services.query_planner import QueryPlanner
from max.web_intelligence.services.research_planner import ResearchPlanner
from max.web_intelligence.services.source_discovery import SourceDiscoveryService
from max.web_intelligence.services.synthesis_service import ResearchSynthesisService

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class WebIntelligenceService:
    """Core service facade coordinating web research, search, content acquisition, evidence, and synthesis."""

    def __init__(
        self,
        settings: WebIntelligenceSettings | None = None,
        search_provider: BaseSearchProvider | None = None,
        research_repo: ResearchRepository | None = None,
        source_repo: SourceRepository | None = None,
        evidence_repo: EvidenceRepository | None = None,
        audit_repo: ResearchAuditRepository | None = None,
    ) -> None:
        self.settings = settings or WebIntelligenceSettings()
        self.provider = search_provider or MockSearchProvider()

        self.research_repo = research_repo or ResearchRepository()
        self.source_repo = source_repo or SourceRepository()
        self.evidence_repo = evidence_repo or EvidenceRepository()

        self.audit_service = ResearchAuditService(audit_repo)
        self.planner = ResearchPlanner()
        self.query_planner = QueryPlanner()
        self.discovery = SourceDiscoveryService()
        self.acquirer = ContentAcquisitionService()
        self.extractor = ContentExtractionService(max_content_bytes=self.settings.max_content_bytes)
        self.evidence_svc = EvidenceService()
        self.comparator = EvidenceComparator()
        self.citation_svc = CitationService()
        self.quality_checker = ResearchQualityChecker()
        self.synthesizer = ResearchSynthesisService()

        self._cancelled_ids: set[str] = set()
        self._active_statuses: dict[str, ResearchStatus] = {}

    def get_status(self, research_id: str) -> ResearchStatus:
        """Get current operational status for a research request."""
        if research_id in self._active_statuses:
            return self._active_statuses[research_id]
        res = self.research_repo.get_result(research_id)
        if res:
            return res.status
        req = self.research_repo.get_request(research_id)
        if req:
            return ResearchStatus.CREATED
        raise ResearchNotFoundError(research_id)

    def cancel_research(self, research_id: str) -> None:
        """Cancel an in-flight research request."""
        self._cancelled_ids.add(research_id)
        self._active_statuses[research_id] = ResearchStatus.CANCELLED
        self.audit_service.log(research_id, "RESEARCH_CANCELLED")

    async def execute_research(self, request: ResearchRequest) -> ResearchResult:
        """Execute complete 10-stage research workflow."""
        self.research_repo.save_request(request)
        self._active_statuses[request.id] = ResearchStatus.CREATED
        self.audit_service.log(request.id, "RESEARCH_CREATED", details={"topic": request.objective.topic})

        start_time = _utc_now()

        try:
            # 1. PLANNING
            self._check_cancelled(request.id)
            self._active_statuses[request.id] = ResearchStatus.PLANNING
            plan = self.planner.create_plan(request)
            self.audit_service.log(request.id, "PLANNING_COMPLETED", details={"steps": len(plan.steps)})

            # 2. QUERYING
            self._check_cancelled(request.id)
            self._active_statuses[request.id] = ResearchStatus.QUERYING
            queries = self.query_planner.generate_queries(request)
            self.audit_service.log(request.id, "QUERYING_COMPLETED", details={"queries_count": len(queries)})

            # 3. SEARCHING
            self._check_cancelled(request.id)
            self._active_statuses[request.id] = ResearchStatus.SEARCHING
            sources = await self.discovery.discover_sources(request, queries, self.provider)
            for s in sources:
                self.source_repo.save(s)
            self.audit_service.log(request.id, "SEARCHING_COMPLETED", details={"sources_found": len(sources)})

            # 4. COLLECTING
            self._check_cancelled(request.id)
            self._active_statuses[request.id] = ResearchStatus.COLLECTING
            acquired_docs = []
            max_acq = request.constraints.max_page_acquisitions
            for src in sources[:max_acq]:
                self._check_cancelled(request.id)
                try:
                    doc = await self.acquirer.acquire_source_content(
                        src,
                        allowed_domains=request.scope.allowed_domains,
                        blocked_domains=request.scope.blocked_domains,
                        use_mock=True,
                    )
                    acquired_docs.append(doc)
                except Exception as e:
                    logger.warning(f"Acquisition failed for '{src.metadata.url}': {e}")
            self.audit_service.log(request.id, "COLLECTING_COMPLETED", details={"docs_acquired": len(acquired_docs)})

            # 5. EXTRACTING
            self._check_cancelled(request.id)
            self._active_statuses[request.id] = ResearchStatus.EXTRACTING
            all_evidence: list[Evidence] = []
            for doc in acquired_docs:
                self.extractor.extract_and_section_content(doc)
                src_obj = self.source_repo.get(doc.source_id)
                if src_obj is not None:
                    ev_items = self.evidence_svc.extract_evidence(request, src_obj, doc)
                    for ev in ev_items:
                        self.evidence_repo.save(ev)
                        all_evidence.append(ev)
            self.audit_service.log(request.id, "EXTRACTING_COMPLETED", details={"evidence_count": len(all_evidence)})

            # 6. VALIDATING & CITATION FORMATTING
            self._check_cancelled(request.id)
            self._active_statuses[request.id] = ResearchStatus.VALIDATING
            citations: list[Citation] = []
            for src in sources:
                if src.is_acquired:
                    cit = self.citation_svc.format_citation(src, request.citation_style)
                    self.citation_svc.validate_citation(cit, sources)
                    citations.append(cit)

            # 7. COMPARING
            self._check_cancelled(request.id)
            self._active_statuses[request.id] = ResearchStatus.COMPARING
            conflicts: list[EvidenceConflict] = self.comparator.compare_evidence(request.id, all_evidence, sources)
            self.audit_service.log(request.id, "COMPARING_COMPLETED", details={"conflicts": len(conflicts)})

            # 8. SYNTHESIZING
            self._check_cancelled(request.id)
            self._active_statuses[request.id] = ResearchStatus.SYNTHESIZING
            quality_report = self.quality_checker.evaluate_quality(request, sources, citations, conflicts)
            synthesis = self.synthesizer.synthesize(request, sources, all_evidence, citations, conflicts, quality_report)

            # 9. COMPLETED
            end_time = _utc_now()
            duration = (end_time - start_time).total_seconds()
            final_status = ResearchStatus.COMPLETED if sources else ResearchStatus.PARTIALLY_COMPLETED

            self._active_statuses[request.id] = final_status

            result = ResearchResult(
                research_id=request.id,
                objective=request.objective,
                status=final_status,
                mode=request.mode,
                depth=request.depth,
                synthesis=synthesis,
                sources=sources,
                evidence=all_evidence,
                queries_used=queries,
                created_at=start_time,
                completed_at=end_time,
                total_duration_seconds=duration,
            )

            self.research_repo.save_result(result)
            self.audit_service.log(request.id, "RESEARCH_COMPLETED", details={"duration": duration, "status": final_status.value})
            return result

        except ResearchCancelledError:
            self._active_statuses[request.id] = ResearchStatus.CANCELLED
            result = ResearchResult(
                research_id=request.id,
                objective=request.objective,
                status=ResearchStatus.CANCELLED,
                mode=request.mode,
                depth=request.depth,
                synthesis=self.synthesizer.synthesize(
                    request, [], [], [], [], self.quality_checker.evaluate_quality(request, [], [], [])
                ),
                created_at=start_time,
            )
            self.research_repo.save_result(result)
            return result

    def _check_cancelled(self, research_id: str) -> None:
        if research_id in self._cancelled_ids:
            raise ResearchCancelledError(research_id)
