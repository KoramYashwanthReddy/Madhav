"""Domain models for filesystem paths, entries, metadata, results, and trace events."""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from max.filesystem.domain.enums import FileEncoding, FileType


class PathReference(BaseModel):
    """Normalized path reference descriptor."""

    original_path: str = Field(..., description="Original input path string")
    normalized_path: str = Field(..., description="Cleaned normalized path string")
    resolved_path: str = Field(..., description="Fully resolved absolute target path")
    is_absolute: bool = Field(default=True, description="Whether path is absolute")
    file_type: FileType = Field(default=FileType.REGULAR_FILE, description="Resolved file object type")
    is_directory: bool = Field(default=False, description="Whether target is a directory")
    is_symlink: bool = Field(default=False, description="Whether target is a symbolic link")
    symlink_target: str | None = Field(default=None, description="Resolved symlink target path if symlink")
    allowed_root: str | None = Field(default=None, description="Associated allowed root sandbox path")


class FileMetadata(BaseModel):
    """Detailed file entry metadata descriptor."""

    name: str = Field(..., description="Filename including extension")
    path: str = Field(..., description="Normalized absolute file path")
    type: FileType = Field(default=FileType.REGULAR_FILE, description="File object type")
    size: int = Field(default=0, ge=0, description="File size in bytes")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Creation timestamp"
    )
    modified_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Last modification timestamp"
    )
    accessed_at: datetime | None = Field(default=None, description="Last access timestamp")
    is_symlink: bool = Field(default=False, description="Whether path is a symbolic link")
    symlink_target: str | None = Field(default=None, description="Resolved symlink target path if symlink")
    extension: str = Field(default="", description="File extension without dot")
    mime_type: str | None = Field(default=None, description="Inferred MIME type string")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata tags")


class DirectoryMetadata(BaseModel):
    """Detailed directory metadata descriptor."""

    name: str = Field(..., description="Directory name")
    path: str = Field(..., description="Normalized absolute directory path")
    total_files: int = Field(default=0, ge=0, description="Child files count")
    total_subdirectories: int = Field(default=0, ge=0, description="Child subdirectories count")
    total_size_bytes: int = Field(default=0, ge=0, description="Total aggregated size of contents")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Creation timestamp"
    )
    modified_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Last modification timestamp"
    )


class FileSystemEntry(BaseModel):
    """Child entry summary descriptor within a directory listing."""

    name: str = Field(..., description="Entry basename")
    path: str = Field(..., description="Full absolute entry path")
    type: FileType = Field(..., description="Entry file type")
    size: int = Field(default=0, ge=0, description="Entry size in bytes")
    modified_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Last modification timestamp"
    )
    is_symlink: bool = Field(default=False, description="Symlink flag")


class DirectoryListing(BaseModel):
    """Structured directory contents response payload."""

    path: str = Field(..., description="Target directory path")
    entries: list[FileSystemEntry] = Field(default_factory=list, description="Child entries")
    count: int = Field(default=0, ge=0, description="Returned entries count")
    truncated: bool = Field(default=False, description="Whether results were truncated by limit")
    limit: int = Field(default=100, description="Applied maximum page limit")


class FileReadResult(BaseModel):
    """File contents read payload."""

    path: str = Field(..., description="Target file path")
    content: str = Field(..., description="File content payload string")
    encoding: FileEncoding = Field(default=FileEncoding.UTF_8, description="Encoding used to decode content")
    size: int = Field(..., ge=0, description="Total file size in bytes")
    bytes_read: int = Field(..., ge=0, description="Number of bytes actually read")
    truncated: bool = Field(default=False, description="Whether content was truncated due to MAX_READ_BYTES limit")
    binary: bool = Field(default=False, description="Whether file is binary content")


class FileWriteResult(BaseModel):
    """File write or append result payload."""

    path: str = Field(..., description="Target file path")
    bytes_written: int = Field(..., ge=0, description="Number of bytes written")
    created: bool = Field(default=False, description="Whether a new file was created")
    overwritten: bool = Field(default=False, description="Whether an existing file was overwritten")
    hash: str | None = Field(default=None, description="SHA-256 hash of new file content")


class SearchFilter(BaseModel):
    """Directory search filter criteria."""

    query: str | None = Field(default=None, description="Filename match pattern or substring")
    extension: str | None = Field(default=None, description="File extension filter (e.g. '.txt')")
    file_type: FileType | None = Field(default=None, description="File type filter")
    min_size: int | None = Field(default=None, ge=0, description="Minimum file size in bytes")
    max_size: int | None = Field(default=None, ge=0, description="Maximum file size in bytes")
    modified_after: datetime | None = Field(default=None, description="Filter files modified after timestamp")
    modified_before: datetime | None = Field(default=None, description="Filter files modified before timestamp")
    max_results: int = Field(default=1000, ge=1, le=5000, description="Maximum search results count")
    max_depth: int = Field(default=20, ge=1, le=50, description="Maximum directory search depth")


class SearchResultEntry(BaseModel):
    """Single match entry in search results."""

    path: str = Field(..., description="Absolute path of matched entry")
    type: FileType = Field(..., description="Matched entry file type")
    size: int = Field(default=0, ge=0, description="Matched file size in bytes")
    modified_at: datetime = Field(..., description="Modification timestamp")


class SearchResponseData(BaseModel):
    """Consolidated filesystem search response payload."""

    query: str | None = Field(default=None, description="Search query string")
    root_path: str = Field(..., description="Target search root directory")
    results: list[SearchResultEntry] = Field(default_factory=list, description="Matched search entries")
    count: int = Field(default=0, ge=0, description="Total results count")
    truncated: bool = Field(default=False, description="Whether result set was truncated by limit")
    limit_reached: bool = Field(default=False, description="Whether search depth/max limit was reached")
    duration_seconds: float = Field(default=0.0, description="Search duration in seconds")


class HashResult(BaseModel):
    """File hash calculation payload."""

    path: str = Field(..., description="Target file path")
    algorithm: str = Field(default="SHA-256", description="Hash algorithm used ('SHA-256', 'SHA-512', 'MD5')")
    hash_value: str = Field(..., description="Hexadecimal digest hash string")
    size: int = Field(..., ge=0, description="File size in bytes")


class CompareResult(BaseModel):
    """Deterministic comparison result between two file paths."""

    path_a: str = Field(..., description="First file path")
    path_b: str = Field(..., description="Second file path")
    identical: bool = Field(..., description="Whether both files have identical content")
    size_match: bool = Field(..., description="Whether file sizes match")
    hash_match: bool = Field(..., description="Whether file hashes match")
    difference_summary: str = Field(default="", description="Summary explanation of comparison outcome")


class FilesystemTraceEvent(BaseModel):
    """Immutable audit trace log event for filesystem operations."""

    event_id: str = Field(
        default_factory=lambda: f"fevt_{uuid.uuid4().hex[:12]}",
        description="Unique trace event identifier",
    )
    operation_id: str | None = Field(default=None, description="Associated file operation ID if applicable")
    event_type: str = Field(..., description="Trace event type (e.g. FILE_OPERATION_STARTED)")
    agent_id: str | None = Field(default=None, description="Originating agent ID")
    details: dict[str, Any] = Field(default_factory=dict, description="Sanitized trace details")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Event timestamp"
    )
