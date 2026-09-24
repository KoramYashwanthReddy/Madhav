"""FastAPI router for Module 22 — Coding Agent."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from max.coding.container import get_coding_container
from max.coding.domain.enums import ChangeType
from max.coding.domain.exceptions import CodingSessionNotFoundError
from max.coding.domain.models import (
    ChangeSet,
    CodePlan,
    CodeReview,
    CodingRequest,
    CodingResult,
    CodingSession,
    RepositoryContext,
    TestRun,
)

router = APIRouter(prefix="/coding", tags=["Coding Agent"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, Any]:
    """Return Coding Agent subsystem health status."""
    container = get_coding_container()
    return {
        "status": "healthy",
        "subsystem": "coding_agent",
        "enabled": container.settings.enabled,
    }


@router.post("/sessions", response_model=CodingSession, status_code=status.HTTP_201_CREATED)
async def create_coding_session(request: CodingRequest) -> CodingSession:
    """Create a new Coding Session and analyze target repository."""
    container = get_coding_container()
    return await container.service.create_session(request)


@router.get("/sessions", response_model=list[CodingSession])
async def list_coding_sessions(owner_id: str | None = Query(default=None)) -> list[CodingSession]:
    """List active coding sessions."""
    container = get_coding_container()
    return container.service.session_repo.list_all(owner_id=owner_id)


@router.get("/sessions/{session_id}", response_model=CodingSession)
async def get_coding_session(session_id: str) -> CodingSession:
    """Get coding session details by ID."""
    container = get_coding_container()
    try:
        return container.service.get_session(session_id)
    except CodingSessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Coding session '{session_id}' not found.")


@router.delete("/sessions/{session_id}", status_code=status.HTTP_200_OK)
async def delete_coding_session(session_id: str) -> dict[str, str]:
    """Delete a coding session."""
    container = get_coding_container()
    if container.service.session_repo.delete(session_id):
        return {"session_id": session_id, "status": "DELETED"}
    raise HTTPException(status_code=404, detail=f"Coding session '{session_id}' not found.")


@router.post("/sessions/{session_id}/analyze", response_model=RepositoryContext)
async def analyze_repository(session_id: str) -> RepositoryContext:
    """Re-analyze target repository for session."""
    container = get_coding_container()
    session = container.service.get_session(session_id)
    context = await container.service.repo_analyzer.analyze_repository(session.request.repo_path)
    session.context = context
    return context


@router.post("/sessions/{session_id}/plan", response_model=CodePlan)
async def plan_coding_task(session_id: str) -> CodePlan:
    """Formulate implementation plan for session objective."""
    container = get_coding_container()
    session = container.service.get_session(session_id)
    plan = container.service.planner.create_plan(session.request)
    session.plan = plan
    return plan


@router.post("/sessions/{session_id}/changes/preview", response_model=ChangeSet)
async def create_patch_changeset(
    session_id: str,
    file_path: str,
    new_content: str,
    change_type: ChangeType = ChangeType.MODIFY_FILE,
) -> ChangeSet:
    """Create a patch ChangeSet preview."""
    container = get_coding_container()
    try:
        return await container.service.create_patch_changeset(
            session_id=session_id,
            file_path=file_path,
            new_content=new_content,
            change_type=change_type,
        )
    except CodingSessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Coding session '{session_id}' not found.")


@router.post("/sessions/{session_id}/changes/apply", response_model=ChangeSet)
async def apply_changeset(session_id: str, changeset_id: str) -> ChangeSet:
    """Apply a ChangeSet to target repository."""
    container = get_coding_container()
    try:
        return await container.service.apply_changeset(session_id, changeset_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/{session_id}/rollback", status_code=status.HTTP_200_OK)
async def rollback_changeset(session_id: str, changeset_id: str) -> dict[str, str]:
    """Rollback an applied ChangeSet."""
    container = get_coding_container()
    try:
        await container.service.rollback_changeset(session_id, changeset_id)
        return {"session_id": session_id, "changeset_id": changeset_id, "status": "ROLLED_BACK"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/{session_id}/validate", response_model=CodingResult)
async def validate_session(session_id: str) -> CodingResult:
    """Execute complete validation pipeline for coding session."""
    container = get_coding_container()
    try:
        return await container.service.validate_session(session_id)
    except CodingSessionNotFoundError:
        raise HTTPException(status_code=404, detail=f"Coding session '{session_id}' not found.")


@router.get("/sessions/{session_id}/status")
async def get_session_status(session_id: str) -> dict[str, str]:
    """Retrieve current operational status of coding session."""
    container = get_coding_container()
    session = container.service.get_session(session_id)
    return {"session_id": session_id, "status": session.status.value}
