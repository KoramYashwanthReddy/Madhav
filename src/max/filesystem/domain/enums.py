"""Enumerations for Module 17 — Filesystem Agent."""

from enum import StrEnum
from typing import Any


class _CaseInsensitiveStrEnum(StrEnum):
    """Base StrEnum performing case-insensitive value matching."""

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            val_norm = value.upper().replace("-", "_")
            for member in cls:
                if member.value.upper().replace("-", "_") == val_norm:
                    return member
        return None


class FileType(_CaseInsensitiveStrEnum):
    """Normalized filesystem object taxonomy."""

    REGULAR_FILE = "REGULAR_FILE"
    DIRECTORY = "DIRECTORY"
    SYMLINK = "SYMLINK"
    SOCKET = "SOCKET"
    DEVICE = "DEVICE"
    UNKNOWN = "UNKNOWN"


class FileOperationType(_CaseInsensitiveStrEnum):
    """Explicit filesystem operations."""

    EXISTS = "EXISTS"
    STAT = "STAT"
    LIST_DIRECTORY = "LIST_DIRECTORY"
    READ_FILE = "READ_FILE"
    WRITE_FILE = "WRITE_FILE"
    APPEND_FILE = "APPEND_FILE"
    CREATE_FILE = "CREATE_FILE"
    CREATE_DIRECTORY = "CREATE_DIRECTORY"
    COPY_FILE = "COPY_FILE"
    COPY_DIRECTORY = "COPY_DIRECTORY"
    MOVE = "MOVE"
    RENAME = "RENAME"
    DELETE_FILE = "DELETE_FILE"
    DELETE_DIRECTORY = "DELETE_DIRECTORY"
    RECURSIVE_DELETE = "RECURSIVE_DELETE"
    SEARCH = "SEARCH"
    HASH = "HASH"
    COMPARE = "COMPARE"


class FileOperationStatus(_CaseInsensitiveStrEnum):
    """Lifecycle status of a filesystem operation."""

    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    AUTHORIZED = "AUTHORIZED"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"
    BLOCKED = "BLOCKED"
    SIMULATED = "SIMULATED"


class FileFailureReason(_CaseInsensitiveStrEnum):
    """Structured failure categorization for filesystem operations."""

    INVALID_OPERATION = "INVALID_OPERATION"
    INVALID_PATH = "INVALID_PATH"
    PATH_NOT_FOUND = "PATH_NOT_FOUND"
    PATH_TRAVERSAL = "PATH_TRAVERSAL"
    PROTECTED_PATH = "PROTECTED_PATH"
    SANDBOX_VIOLATION = "SANDBOX_VIOLATION"
    SYMLINK_ESCAPE = "SYMLINK_ESCAPE"
    FILE_EXISTS = "FILE_EXISTS"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    PERMISSION_EXPIRED = "PERMISSION_EXPIRED"
    SECURITY_BLOCKED = "SECURITY_BLOCKED"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    SEARCH_LIMIT_EXCEEDED = "SEARCH_LIMIT_EXCEEDED"
    BACKEND_UNAVAILABLE = "BACKEND_UNAVAILABLE"
    OS_ERROR = "OS_ERROR"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class FilesystemCapability(_CaseInsensitiveStrEnum):
    """Filesystem capability classification tags."""

    FILESYSTEM_READ = "FILESYSTEM_READ"
    FILESYSTEM_WRITE = "FILESYSTEM_WRITE"
    FILESYSTEM_CREATE = "FILESYSTEM_CREATE"
    FILESYSTEM_DELETE = "FILESYSTEM_DELETE"
    FILESYSTEM_DELETE_RECURSIVE = "FILESYSTEM_DELETE_RECURSIVE"
    FILESYSTEM_MOVE = "FILESYSTEM_MOVE"
    FILESYSTEM_COPY = "FILESYSTEM_COPY"
    FILESYSTEM_SEARCH = "FILESYSTEM_SEARCH"
    FILESYSTEM_METADATA = "FILESYSTEM_METADATA"
    FILESYSTEM_HASH = "FILESYSTEM_HASH"
    FILESYSTEM_COMPARE = "FILESYSTEM_COMPARE"


class FileEncoding(_CaseInsensitiveStrEnum):
    """Text decoding / encoding parameters."""

    UTF_8 = "UTF_8"
    ASCII = "ASCII"
    LATIN_1 = "LATIN_1"
    BINARY = "BINARY"
