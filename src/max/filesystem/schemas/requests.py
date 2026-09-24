"""Pydantic request schemas for API endpoints of Module 17 Filesystem Agent."""

from typing import Any

from pydantic import BaseModel, Field


class PathRequest(BaseModel):
    """Base request specifying a single target path."""

    path: str = Field(..., description="Target filesystem path")
    owner_id: str = Field(default="system", description="Owner identifier")
    agent_id: str = Field(default="agent_fs", description="Agent identifier")
    dry_run: bool = Field(default=False, description="Simulate without mutating filesystem")


class ExistsRequest(PathRequest):
    """Request to check existence of file or directory."""

    pass


class StatRequest(PathRequest):
    """Request to inspect metadata of path."""

    pass


class ListDirectoryRequest(PathRequest):
    """Request to list directory contents."""

    pass


class ReadFileRequest(PathRequest):
    """Request to read content from file."""

    encoding: str = Field(default="utf-8", description="Encoding for text files")
    max_bytes: int = Field(default=10_485_760, description="Maximum bytes to read")
    offset: int = Field(default=0, description="Offset byte position")


class WriteFileRequest(PathRequest):
    """Request to write text or binary content to file."""

    content: str = Field(..., description="File content to write")
    encoding: str = Field(default="utf-8", description="Encoding")
    overwrite: bool = Field(default=True, description="Allow overwriting existing file")
    atomic: bool = Field(default=True, description="Perform atomic write via temp file")


class AppendFileRequest(PathRequest):
    """Request to append content to an existing file."""

    content: str = Field(..., description="Content to append")
    encoding: str = Field(default="utf-8", description="Encoding")


class CreateFileRequest(PathRequest):
    """Request to create a new file."""

    content: str = Field(default="", description="Initial content")
    overwrite: bool = Field(default=False, description="Fail if file exists unless True")


class CreateDirectoryRequest(PathRequest):
    """Request to create a directory."""

    parents: bool = Field(default=True, description="Create missing parent directories")


class DualPathRequest(BaseModel):
    """Request involving a source and destination path."""

    source_path: str = Field(..., description="Source path")
    destination_path: str = Field(..., description="Destination path")
    owner_id: str = Field(default="system", description="Owner identifier")
    agent_id: str = Field(default="agent_fs", description="Agent identifier")
    dry_run: bool = Field(default=False, description="Simulate without mutating")


class CopyRequest(DualPathRequest):
    """Request to copy a file or directory."""

    is_directory: bool = Field(default=False, description="Whether target is a directory")
    overwrite: bool = Field(default=False, description="Allow destination overwrite")


class MoveRequest(DualPathRequest):
    """Request to move a file or directory."""

    overwrite: bool = Field(default=False, description="Allow destination overwrite")


class RenameRequest(DualPathRequest):
    """Request to rename a file or directory."""

    overwrite: bool = Field(default=False, description="Allow destination overwrite")


class DeleteRequest(PathRequest):
    """Request to delete a file or directory."""

    is_directory: bool = Field(default=False, description="Set True if target is a directory")
    recursive: bool = Field(default=False, description="Explicit recursive deletion flag for directories")
    confirmation_reason: str | None = Field(default=None, description="Reason for deletion confirmation")


class SearchRequest(PathRequest):
    """Request to search filesystem paths."""

    pattern: str = Field(default="*", description="Glob search pattern")
    recursive: bool = Field(default=True, description="Search subdirectories recursively")
    max_depth: int = Field(default=10, description="Maximum directory search depth")
    max_results: int = Field(default=1000, description="Maximum search results count")


class HashRequest(PathRequest):
    """Request to calculate file cryptographic hash."""

    algorithm: str = Field(default="sha256", description="Hash algorithm (sha256, sha512, md5)")


class CompareRequest(DualPathRequest):
    """Request to compare two files."""

    pass


class RawOperationRequest(BaseModel):
    """Generic raw operation request schema."""

    operation_type: str = Field(..., description="Operation type name")
    source_path: str = Field(..., description="Primary path")
    destination_path: str | None = Field(default=None, description="Optional destination path")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Operation specific parameters")
    owner_id: str = Field(default="system", description="Owner identifier")
    agent_id: str = Field(default="agent_fs", description="Agent identifier")
