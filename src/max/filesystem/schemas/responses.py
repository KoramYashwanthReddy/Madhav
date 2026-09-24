"""Pydantic response schemas for API endpoints of Module 17 Filesystem Agent."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StatusResponse(BaseModel):
    """Filesystem Agent status and capabilities response."""

    enabled: bool
    dry_run: bool
    backend_type: str
    allowed_roots: List[str]
    read_only_roots: List[str]
    blocked_roots: List[str]
    capabilities: List[str]
    permission_gate_active: bool


class PathExistsResponse(BaseModel):
    """Response for file/directory existence check."""

    path: str
    exists: bool


class FileMetadataResponse(BaseModel):
    """Response containing detailed metadata of a file or directory."""

    name: str
    path: str
    type: str
    size: int
    created_at: str
    modified_at: str
    accessed_at: Optional[str] = None
    extension: str = ""
    mime_type: Optional[str] = None
    is_symlink: bool = False
    symlink_target: Optional[str] = None


class DirectoryEntrySchema(BaseModel):
    """Entry in directory listing response."""

    name: str
    path: str
    type: str
    size: int
    modified_at: str
    extension: str = ""
    is_symlink: bool = False


class DirectoryResponse(BaseModel):
    """Response for directory listing."""

    path: str
    entries: List[DirectoryEntrySchema]
    count: int
    truncated: bool = False
    limit: int = 100


class ReadFileResponse(BaseModel):
    """Response for read_file operation."""

    path: str
    content: str
    encoding: str
    size: int
    bytes_read: int
    truncated: bool = False
    binary: bool = False


class WriteFileResponse(BaseModel):
    """Response for write or append operations."""

    path: str
    bytes_written: int
    created: bool = False
    overwritten: bool = False
    hash: Optional[str] = None


class SearchEntrySchema(BaseModel):
    """Single matching entry in search response."""

    path: str
    type: str
    size: int
    modified_at: str


class SearchResponse(BaseModel):
    """Response for filesystem search."""

    root_path: str
    query: Optional[str] = None
    results: List[SearchEntrySchema]
    count: int
    truncated: bool = False
    limit_reached: bool = False
    duration_seconds: float = 0.0


class HashResponse(BaseModel):
    """Response for file hashing."""

    path: str
    algorithm: str
    hash_value: str
    size: int


class CompareResponse(BaseModel):
    """Response for file comparison."""

    path_a: str
    path_b: str
    identical: bool
    size_match: bool
    hash_match: bool
    difference_summary: str = ""


class FileOperationFailureResponse(BaseModel):
    """Structured failure detail."""

    operation_id: str
    operation_type: str
    reason: str
    message: str
    timestamp: str
    details: Dict[str, Any] = Field(default_factory=dict)


class FileOperationResponse(BaseModel):
    """Unified file operation lifecycle response."""

    operation_id: str
    operation_type: str
    status: str
    source: str
    destination: Optional[str] = None
    duration: float = 0.0
    observed_state: Dict[str, Any] = Field(default_factory=dict)
    failure: Optional[FileOperationFailureResponse] = None
