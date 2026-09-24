"""FastAPI routes for Module 17 — Filesystem Agent."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status

from max.filesystem.container import get_filesystem_container
from max.filesystem.domain.action import FileOperationRequest
from max.filesystem.domain.enums import FileOperationType
from max.filesystem.schemas.requests import (
    AppendFileRequest,
    CompareRequest,
    CopyRequest,
    CreateDirectoryRequest,
    CreateFileRequest,
    DeleteRequest,
    ExistsRequest,
    HashRequest,
    ListDirectoryRequest,
    MoveRequest,
    RawOperationRequest,
    ReadFileRequest,
    RenameRequest,
    SearchRequest,
    StatRequest,
    WriteFileRequest,
)
from max.filesystem.schemas.responses import (
    FileOperationResponse,
    StatusResponse,
)

router = APIRouter(prefix="/filesystem", tags=["filesystem"])


def _op_req(
    op_type: FileOperationType,
    source: str,
    dest: str | None = None,
    params: dict[str, Any] | None = None,
    owner_id: str = "system",
    agent_id: str = "agent_fs",
) -> FileOperationRequest:
    return FileOperationRequest(
        operation_id=f"op_{uuid.uuid4().hex[:12]}",
        operation_type=op_type,
        source=source,
        destination=dest,
        parameters=params or {},
        owner_id=owner_id,
        agent_id=agent_id,
    )


@router.get("/status", response_model=StatusResponse)
def get_status() -> StatusResponse:
    """Get operational status and configuration of Filesystem Agent."""
    service = get_filesystem_container().filesystem_service
    return StatusResponse(**service.get_status())


@router.get("/config")
def get_config() -> dict[str, Any]:
    """Get active filesystem settings configuration."""
    container = get_filesystem_container()
    return container.settings.model_dump(mode="json")


@router.post("/exists", response_model=FileOperationResponse)
def check_exists(req: ExistsRequest) -> FileOperationResponse:
    """Check if file or directory exists."""
    service = get_filesystem_container().filesystem_service
    op = _op_req(FileOperationType.EXISTS, req.path, params={"dry_run": req.dry_run}, owner_id=req.owner_id, agent_id=req.agent_id)
    res = service.execute_operation(op)
    return FileOperationResponse(**res.model_dump(mode="json"))


@router.post("/stat", response_model=FileOperationResponse)
def get_stat(req: StatRequest) -> FileOperationResponse:
    """Inspect metadata of file or directory."""
    service = get_filesystem_container().filesystem_service
    op = _op_req(FileOperationType.STAT, req.path, params={"dry_run": req.dry_run}, owner_id=req.owner_id, agent_id=req.agent_id)
    res = service.execute_operation(op)
    return FileOperationResponse(**res.model_dump(mode="json"))


@router.post("/list", response_model=FileOperationResponse)
def list_directory(req: ListDirectoryRequest) -> FileOperationResponse:
    """List entries in directory."""
    service = get_filesystem_container().filesystem_service
    op = _op_req(FileOperationType.LIST_DIRECTORY, req.path, params={"dry_run": req.dry_run}, owner_id=req.owner_id, agent_id=req.agent_id)
    res = service.execute_operation(op)
    return FileOperationResponse(**res.model_dump(mode="json"))


@router.post("/read", response_model=FileOperationResponse)
def read_file(req: ReadFileRequest) -> FileOperationResponse:
    """Read text or binary file content safely with byte limits."""
    service = get_filesystem_container().filesystem_service
    op = _op_req(
        FileOperationType.READ_FILE,
        req.path,
        params={"encoding": req.encoding, "max_bytes": req.max_bytes, "offset": req.offset, "dry_run": req.dry_run},
        owner_id=req.owner_id,
        agent_id=req.agent_id,
    )
    res = service.execute_operation(op)
    return FileOperationResponse(**res.model_dump(mode="json"))


@router.post("/create", response_model=FileOperationResponse)
def create_file(req: CreateFileRequest) -> FileOperationResponse:
    """Create a new file."""
    service = get_filesystem_container().filesystem_service
    op = _op_req(
        FileOperationType.CREATE_FILE,
        req.path,
        params={"content": req.content, "overwrite": req.overwrite, "dry_run": req.dry_run},
        owner_id=req.owner_id,
        agent_id=req.agent_id,
    )
    res = service.execute_operation(op)
    return FileOperationResponse(**res.model_dump(mode="json"))


@router.post("/mkdir", response_model=FileOperationResponse)
def create_directory(req: CreateDirectoryRequest) -> FileOperationResponse:
    """Create a new directory."""
    service = get_filesystem_container().filesystem_service
    op = _op_req(
        FileOperationType.CREATE_DIRECTORY,
        req.path,
        params={"parents": req.parents, "dry_run": req.dry_run},
        owner_id=req.owner_id,
        agent_id=req.agent_id,
    )
    res = service.execute_operation(op)
    return FileOperationResponse(**res.model_dump(mode="json"))


@router.post("/write", response_model=FileOperationResponse)
def write_file(req: WriteFileRequest) -> FileOperationResponse:
    """Write text or binary content to file (atomic write supported)."""
    service = get_filesystem_container().filesystem_service
    op = _op_req(
        FileOperationType.WRITE_FILE,
        req.path,
        params={"content": req.content, "encoding": req.encoding, "overwrite": req.overwrite, "atomic": req.atomic, "dry_run": req.dry_run},
        owner_id=req.owner_id,
        agent_id=req.agent_id,
    )
    res = service.execute_operation(op)
    return FileOperationResponse(**res.model_dump(mode="json"))


@router.post("/append", response_model=FileOperationResponse)
def append_file(req: AppendFileRequest) -> FileOperationResponse:
    """Append content to file."""
    service = get_filesystem_container().filesystem_service
    op = _op_req(
        FileOperationType.APPEND_FILE,
        req.path,
        params={"content": req.content, "encoding": req.encoding, "dry_run": req.dry_run},
        owner_id=req.owner_id,
        agent_id=req.agent_id,
    )
    res = service.execute_operation(op)
    return FileOperationResponse(**res.model_dump(mode="json"))


@router.post("/copy", response_model=FileOperationResponse)
def copy_file_or_dir(req: CopyRequest) -> FileOperationResponse:
    """Copy file or directory."""
    service = get_filesystem_container().filesystem_service
    op_type = FileOperationType.COPY_DIRECTORY if req.is_directory else FileOperationType.COPY_FILE
    op = _op_req(
        op_type,
        req.source_path,
        dest=req.destination_path,
        params={"overwrite": req.overwrite, "dry_run": req.dry_run},
        owner_id=req.owner_id,
        agent_id=req.agent_id,
    )
    res = service.execute_operation(op)
    return FileOperationResponse(**res.model_dump(mode="json"))


@router.post("/move", response_model=FileOperationResponse)
def move_file_or_dir(req: MoveRequest) -> FileOperationResponse:
    """Move file or directory."""
    service = get_filesystem_container().filesystem_service
    op = _op_req(
        FileOperationType.MOVE,
        req.source_path,
        dest=req.destination_path,
        params={"overwrite": req.overwrite, "dry_run": req.dry_run},
        owner_id=req.owner_id,
        agent_id=req.agent_id,
    )
    res = service.execute_operation(op)
    return FileOperationResponse(**res.model_dump(mode="json"))


@router.post("/rename", response_model=FileOperationResponse)
def rename_file_or_dir(req: RenameRequest) -> FileOperationResponse:
    """Rename file or directory."""
    service = get_filesystem_container().filesystem_service
    op = _op_req(
        FileOperationType.RENAME,
        req.source_path,
        dest=req.destination_path,
        params={"overwrite": req.overwrite, "dry_run": req.dry_run},
        owner_id=req.owner_id,
        agent_id=req.agent_id,
    )
    res = service.execute_operation(op)
    return FileOperationResponse(**res.model_dump(mode="json"))


@router.post("/delete", response_model=FileOperationResponse)
def delete_file_or_dir(req: DeleteRequest) -> FileOperationResponse:
    """Delete file or directory safely."""
    service = get_filesystem_container().filesystem_service
    op_type = FileOperationType.DELETE_DIRECTORY if req.is_directory else FileOperationType.DELETE_FILE
    op = _op_req(
        op_type,
        req.path,
        params={"recursive": req.recursive, "confirmation_reason": req.confirmation_reason, "dry_run": req.dry_run},
        owner_id=req.owner_id,
        agent_id=req.agent_id,
    )
    res = service.execute_operation(op)
    return FileOperationResponse(**res.model_dump(mode="json"))


@router.post("/search", response_model=FileOperationResponse)
def search_files(req: SearchRequest) -> FileOperationResponse:
    """Search filesystem within allowed roots."""
    service = get_filesystem_container().filesystem_service
    op = _op_req(
        FileOperationType.SEARCH,
        req.path,
        params={
            "pattern": req.pattern,
            "recursive": req.recursive,
            "max_depth": req.max_depth,
            "max_results": req.max_results,
            "dry_run": req.dry_run,
        },
        owner_id=req.owner_id,
        agent_id=req.agent_id,
    )
    res = service.execute_operation(op)
    return FileOperationResponse(**res.model_dump(mode="json"))


@router.post("/hash", response_model=FileOperationResponse)
def hash_file(req: HashRequest) -> FileOperationResponse:
    """Calculate cryptographic hash of file."""
    service = get_filesystem_container().filesystem_service
    op = _op_req(
        FileOperationType.HASH,
        req.path,
        params={"algorithm": req.algorithm, "dry_run": req.dry_run},
        owner_id=req.owner_id,
        agent_id=req.agent_id,
    )
    res = service.execute_operation(op)
    return FileOperationResponse(**res.model_dump(mode="json"))


@router.post("/compare", response_model=FileOperationResponse)
def compare_files(req: CompareRequest) -> FileOperationResponse:
    """Compare two files by size, hash, and content."""
    service = get_filesystem_container().filesystem_service
    op = _op_req(
        FileOperationType.COMPARE,
        req.source_path,
        dest=req.destination_path,
        params={"dry_run": req.dry_run},
        owner_id=req.owner_id,
        agent_id=req.agent_id,
    )
    res = service.execute_operation(op)
    return FileOperationResponse(**res.model_dump(mode="json"))


@router.post("/operations", response_model=FileOperationResponse)
def submit_raw_operation(req: RawOperationRequest) -> FileOperationResponse:
    """Submit a generic raw operation request."""
    service = get_filesystem_container().filesystem_service
    try:
        op_enum = FileOperationType(req.operation_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown operation_type '{req.operation_type}'",
        ) from exc
    op = _op_req(
        op_enum,
        req.source_path,
        dest=req.destination_path,
        params=req.parameters,
        owner_id=req.owner_id,
        agent_id=req.agent_id,
    )
    res = service.execute_operation(op)
    return FileOperationResponse(**res.model_dump(mode="json"))


@router.get("/operations", response_model=list[FileOperationResponse])
def list_operations() -> list[FileOperationResponse]:
    """List recent file operations."""
    container = get_filesystem_container()
    ops = container.operation_repo.list_all(limit=100)
    out: list[FileOperationResponse] = []
    for op in ops:
        if op.result:
            out.append(FileOperationResponse(**op.result.model_dump(mode="json")))
    return out


@router.get("/operations/{operation_id}", response_model=FileOperationResponse)
def get_operation(operation_id: str) -> FileOperationResponse:
    """Get details of a specific operation by ID."""
    container = get_filesystem_container()
    op = container.operation_repo.get(operation_id)
    if not op or not op.result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operation '{operation_id}' not found.",
        )
    return FileOperationResponse(**op.result.model_dump(mode="json"))


@router.post("/operations/{operation_id}/cancel", response_model=dict[str, Any])
def cancel_operation(operation_id: str) -> dict[str, Any]:
    """Cancel a running or pending operation."""
    container = get_filesystem_container()
    op = container.operation_repo.get(operation_id)
    if not op:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operation '{operation_id}' not found.",
        )
    from max.filesystem.domain.enums import FileOperationStatus

    op.status = FileOperationStatus.CANCELLED
    container.operation_repo.save(op)
    return {"operation_id": operation_id, "status": "CANCELLED"}
