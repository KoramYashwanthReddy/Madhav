"""REST API endpoints for Module 08 Memory Engine."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from max.memory.domain.enums import MemoryImportance, MemorySource, MemoryStatus, MemoryType
from max.memory.domain.filter import MemorySearchFilter
from max.memory.domain.metadata import MemoryMetadata
from max.memory.domain.summary import MemorySummary
from max.memory.exceptions import MemoryEngineError
from max.memory.schemas.requests import (
    CreateMemoryRequest,
    MemorySearchRequest,
    UpdateMemoryRequest,
)
from max.memory.schemas.responses import (
    MemoryListResponse,
    MemoryResponse,
    MemorySummaryResponse,
)
from max.memory.services.memory_service import MemoryService

router = APIRouter(prefix="/memories", tags=["Memory Engine"])

_memory_service_instance: MemoryService | None = None


def get_memory_service() -> MemoryService:
    """Dependency provider returning singleton MemoryService instance."""
    global _memory_service_instance
    if _memory_service_instance is None:
        _memory_service_instance = MemoryService()
    return _memory_service_instance


def set_memory_service(service: MemoryService | None) -> None:
    """Helper to set or reset singleton MemoryService instance (useful for test isolation)."""
    global _memory_service_instance
    _memory_service_instance = service


@router.post(
    "",
    response_model=MemoryResponse,
    status_code=201,
    summary="Create a new memory record",
    description="Persist a new structured memory record with duplicate check.",
)
async def create_memory(
    req: CreateMemoryRequest,
    service: MemoryService = Depends(get_memory_service),
) -> MemoryResponse:
    """Create memory endpoint."""
    try:
        metadata = MemoryMetadata(
            source_reference=req.source_reference,
            conversation_id=req.conversation_id,
            message_id=req.message_id,
            tags=req.tags,
            custom_metadata=req.custom_metadata,
        )
        mem = await service.create_memory(
            owner_id="default_owner",
            type=req.type,
            text=req.text,
            structured_data=req.structured_data,
            importance=req.importance,
            confidence=req.confidence,
            source=req.source,
            metadata=metadata,
            expires_at=req.expires_at,
            check_duplicate=req.check_duplicate,
        )
        return MemoryResponse.from_domain(mem)
    except MemoryEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.get(
    "",
    response_model=MemoryListResponse,
    summary="List memories",
    description="Retrieve paginated memory records with optional filter parameters.",
)
async def list_memories(
    type: MemoryType | None = Query(default=None, description="Optional type filter"),
    status: MemoryStatus | None = Query(default=None, description="Optional status filter"),
    importance: MemoryImportance | None = Query(
        default=None, description="Optional importance filter"
    ),
    source: MemorySource | None = Query(default=None, description="Optional source filter"),
    limit: int = Query(default=50, ge=1, le=200, description="Page limit"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
    service: MemoryService = Depends(get_memory_service),
) -> MemoryListResponse:
    """List memories endpoint."""
    try:
        types_list = [type] if type else None
        statuses_list = [status] if status else None
        importances_list = [importance] if importance else None
        sources_list = [source] if source else None

        filter_spec = MemorySearchFilter(
            owner_id="default_owner",
            types=types_list,
            statuses=statuses_list,
            importances=importances_list,
            sources=sources_list,
            limit=limit,
            offset=offset,
        )
        summaries, total = await service.list_memories(filter_spec)
        has_more = (offset + limit) < total

        return MemoryListResponse(
            memories=[MemorySummaryResponse.from_domain(s) for s in summaries],
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more,
        )
    except MemoryEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.post(
    "/search",
    response_model=MemoryListResponse,
    summary="Search memories",
    description="Execute substring text search and filter query across memory records.",
)
async def search_memories(
    req: MemorySearchRequest,
    service: MemoryService = Depends(get_memory_service),
) -> MemoryListResponse:
    """Search memories endpoint."""
    try:
        filter_spec = MemorySearchFilter(
            query=req.query,
            types=req.types,
            statuses=req.statuses,
            importances=req.importances,
            sources=req.sources,
            tags=req.tags,
            owner_id="default_owner",
            include_expired=req.include_expired,
            include_archived=req.include_archived,
            include_deleted=req.include_deleted,
            limit=req.limit,
            offset=req.offset,
        )
        summaries, total = await service.search_memories(filter_spec)
        has_more = (req.offset + req.limit) < total

        return MemoryListResponse(
            memories=[MemorySummaryResponse.from_domain(s) for s in summaries],
            total=total,
            limit=req.limit,
            offset=req.offset,
            has_more=has_more,
        )
    except MemoryEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.get(
    "/{memory_id}",
    response_model=MemoryResponse,
    summary="Get memory by ID",
    description="Retrieve full details for a specific memory record, updating access tracking.",
)
async def get_memory(
    memory_id: UUID,
    service: MemoryService = Depends(get_memory_service),
) -> MemoryResponse:
    """Get memory by ID endpoint."""
    try:
        mem = await service.get_memory(memory_id, owner_id="default_owner", touch_access=True)
        return MemoryResponse.from_domain(mem)
    except MemoryEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.get(
    "/{memory_id}/summary",
    response_model=MemorySummaryResponse,
    summary="Get memory summary",
    description="Retrieve lightweight summary projection for a memory record.",
)
async def get_memory_summary(
    memory_id: UUID,
    service: MemoryService = Depends(get_memory_service),
) -> MemorySummaryResponse:
    """Get memory summary endpoint."""
    try:
        mem = await service.get_memory(memory_id, owner_id="default_owner", touch_access=True)
        summary = MemorySummary.from_memory(mem)
        return MemorySummaryResponse.from_domain(summary)
    except MemoryEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.patch(
    "/{memory_id}",
    response_model=MemoryResponse,
    summary="Update memory record",
    description="Modify text content, importance, confidence, tags, or metadata of a memory.",
)
async def update_memory(
    memory_id: UUID,
    req: UpdateMemoryRequest,
    service: MemoryService = Depends(get_memory_service),
) -> MemoryResponse:
    """Update memory endpoint."""
    try:
        metadata = (
            MemoryMetadata(tags=req.tags or [], custom_metadata=req.custom_metadata or {})
            if (req.tags is not None or req.custom_metadata is not None)
            else None
        )
        updated = await service.update_memory(
            memory_id=memory_id,
            owner_id="default_owner",
            text=req.text,
            structured_data=req.structured_data,
            importance=req.importance,
            confidence=req.confidence,
            tags=req.tags,
            metadata=metadata,
            expires_at=req.expires_at,
        )
        return MemoryResponse.from_domain(updated)
    except MemoryEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.post(
    "/{memory_id}/archive",
    response_model=MemoryResponse,
    summary="Archive memory record",
    description="Transition memory record state to ARCHIVED.",
)
async def archive_memory(
    memory_id: UUID,
    service: MemoryService = Depends(get_memory_service),
) -> MemoryResponse:
    """Archive memory endpoint."""
    try:
        archived = await service.archive_memory(memory_id, owner_id="default_owner")
        return MemoryResponse.from_domain(archived)
    except MemoryEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.post(
    "/{memory_id}/restore",
    response_model=MemoryResponse,
    summary="Restore archived/expired memory",
    description="Transition memory record state back to ACTIVE.",
)
async def restore_memory(
    memory_id: UUID,
    service: MemoryService = Depends(get_memory_service),
) -> MemoryResponse:
    """Restore memory endpoint."""
    try:
        restored = await service.restore_memory(memory_id, owner_id="default_owner")
        return MemoryResponse.from_domain(restored)
    except MemoryEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.post(
    "/{memory_id}/expire",
    response_model=MemoryResponse,
    summary="Explicitly expire memory record",
    description="Transition memory record state to EXPIRED.",
)
async def expire_memory(
    memory_id: UUID,
    service: MemoryService = Depends(get_memory_service),
) -> MemoryResponse:
    """Expire memory endpoint."""
    try:
        expired = await service.expire_memory(memory_id, owner_id="default_owner")
        return MemoryResponse.from_domain(expired)
    except MemoryEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc


@router.delete(
    "/{memory_id}",
    status_code=204,
    summary="Soft delete memory record",
    description="Soft delete a memory record safely.",
)
async def delete_memory(
    memory_id: UUID,
    service: MemoryService = Depends(get_memory_service),
) -> None:
    """Delete memory endpoint."""
    try:
        await service.delete_memory(memory_id, owner_id="default_owner", soft_delete=True)
    except MemoryEngineError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"message": exc.message, "code": exc.code, "details": exc.details},
        ) from exc
