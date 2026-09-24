"""Module 17 — Filesystem Agent package for Max Personal AI System."""

from max.filesystem.backends import (
    FilesystemBackend,
    LocalFilesystemBackend,
    MockFilesystemBackend,
)
from max.filesystem.container import (
    FilesystemContainer,
    get_filesystem_container,
    reset_filesystem_container,
)
from max.filesystem.domain import (
    DirectoryListing,
    DirectoryMetadata,
    FileEncoding,
    FileFailureReason,
    FileMetadata,
    FileOperation,
    FileOperationFailure,
    FileOperationRequest,
    FileOperationResult,
    FileOperationStatus,
    FileOperationType,
    FileReadResult,
    FilesystemCapability,
    FileSystemEntry,
    FilesystemError,
    FilesystemTraceEvent,
    FileType,
    FileWriteResult,
    PathReference,
    PathValidationError,
    ProtectedPathError,
    SandboxViolationError,
    SymlinkEscapeError,
)
from max.filesystem.security import PathSecurityService
from max.filesystem.services import (
    FilesystemMutationService,
    FilesystemObservationService,
    FilesystemService,
    register_filesystem_tools,
)

__all__ = [
    # Backends
    "FilesystemBackend",
    "LocalFilesystemBackend",
    "MockFilesystemBackend",
    # Container
    "FilesystemContainer",
    "get_filesystem_container",
    "reset_filesystem_container",
    # Domain Models & Enums
    "FileType",
    "FileOperationType",
    "FileOperationStatus",
    "FileFailureReason",
    "FilesystemCapability",
    "FileEncoding",
    "PathReference",
    "FileMetadata",
    "DirectoryMetadata",
    "FileSystemEntry",
    "DirectoryListing",
    "FileReadResult",
    "FileWriteResult",
    "FileOperationRequest",
    "FileOperationResult",
    "FileOperationFailure",
    "FileOperation",
    "FilesystemTraceEvent",
    "FilesystemError",
    "PathValidationError",
    "ProtectedPathError",
    "SandboxViolationError",
    "SymlinkEscapeError",
    # Security
    "PathSecurityService",
    # Services
    "FilesystemService",
    "FilesystemObservationService",
    "FilesystemMutationService",
    "register_filesystem_tools",
]
