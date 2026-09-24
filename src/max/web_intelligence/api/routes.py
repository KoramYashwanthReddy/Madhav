"""FastAPI router for Module 21 — Web Intelligence."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from max.web_intelligence.container import get_web_intelligence_container
from max.web_intelligence.domain.exceptions import ResearchNotFoundError
from max.web_intelligence.domain.models import (
    Citation,
    Evidence,
    EvidenceConflict,
    ResearchFinding,
    ResearchRequest,
    ResearchResult,
    SearchRequest,
    SearchResponse,
    Source,
)

router = APIRouter(prefix="/web-intelligence", tags=["Web Intelligence"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, Any]:
    """Return Web Intelligence subsystem operational health status."""
    container = get_web_intelligence_container()
    provider_health = await container.provider.health()
    return {
        "status": "healthy",
        "subsystem": "web_intelligence",
        "enabled": container.settings.enabled,
        "provider": provider_health,
    }


@router.post("/research", response_model=ResearchResult, status_code=status.HTTP_201_CREATED)
async def execute_research(request: ResearchRequest) -> ResearchResult:
    """Submit and execute a multi-step web research request."""
    container = get_web_intelligence_container()
    return await container.service.execute_research(request)


@router.get("/research", response_model=list[ResearchRequest])
async def list_research(owner_id: str | None = Query(default=None)) -> list[ResearchRequest]:
    """List research requests."""
    container = get_web_intelligence_container()
    return container.service.research_repo.list_requests(owner_id=owner_id)


@router.get("/research/{research_id}", response_model=ResearchResult)
async def get_research_result(research_id: str) -> ResearchResult:
    """Retrieve full research result by ID."""
    container = get_web_intelligence_container()
    res = container.service.research_repo.get_result(research_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Research result '{research_id}' not found.")
    return res


@router.post("/research/{research_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_research(research_id: str) -> dict[str, str]:
    """Cancel an active research request."""
    container = get_web_intelligence_container()
    try:
        container.service.cancel_research(research_id)
        return {"research_id": research_id, "status": "CANCELLED"}
    except ResearchNotFoundError:
        raise HTTPException(status_code=404, detail=f"Research request '{research_id}' not found.")


@router.get("/research/{research_id}/status")
async def get_research_status(research_id: str) -> dict[str, str]:
    """Retrieve operational status for a research request."""
    container = get_web_intelligence_container()
    try:
        st = container.service.get_status(research_id)
        return {"research_id": research_id, "status": st.value}
    except ResearchNotFoundError:
        raise HTTPException(status_code=404, detail=f"Research request '{research_id}' not found.")


@router.get("/research/{research_id}/sources", response_model=list[Source])
async def get_research_sources(research_id: str) -> list[Source]:
    """Get discovered candidate sources for a research request."""
    container = get_web_intelligence_container()
    return container.service.source_repo.list_by_research(research_id)


@router.get("/research/{research_id}/findings", response_model=list[ResearchFinding])
async def get_research_findings(research_id: str) -> list[ResearchFinding]:
    """Get synthesized findings for a research request."""
    container = get_web_intelligence_container()
    res = container.service.research_repo.get_result(research_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Research result '{research_id}' not found.")
    return res.synthesis.findings


@router.get("/research/{research_id}/evidence", response_model=list[Evidence])
async def get_research_evidence(research_id: str) -> list[Evidence]:
    """Get extracted evidence items for a research request."""
    container = get_web_intelligence_container()
    return container.service.evidence_repo.list_by_research(research_id)


@router.get("/research/{research_id}/citations", response_model=list[Citation])
async def get_research_citations(research_id: str) -> list[Citation]:
    """Get formatted citations for a research request."""
    container = get_web_intelligence_container()
    res = container.service.research_repo.get_result(research_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Research result '{research_id}' not found.")
    return res.synthesis.citations


@router.get("/research/{research_id}/conflicts", response_model=list[EvidenceConflict])
async def get_research_conflicts(research_id: str) -> list[EvidenceConflict]:
    """Get detected source conflicts for a research request."""
    container = get_web_intelligence_container()
    res = container.service.research_repo.get_result(research_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Research result '{research_id}' not found.")
    return res.synthesis.conflicts


@router.post("/search", response_model=SearchResponse)
async def execute_direct_search(request: SearchRequest) -> SearchResponse:
    """Execute direct search query via configured search provider."""
    container = get_web_intelligence_container()
    return await container.provider.search(request)


@router.get("/sources/{source_id}", response_model=Source)
async def get_source_details(source_id: str) -> Source:
    """Retrieve details for a specific source."""
    container = get_web_intelligence_container()
    src = container.service.source_repo.get(source_id)
    if not src:
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found.")
    return src
