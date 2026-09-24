"""Domain exceptions for Module 17 — Filesystem Agent."""

from typing import Any

from max.core.exceptions import MaxException


class FilesystemError(MaxException):
    """Base exception for all filesystem operations."""

    def __init__(
        self,
        message: str = "A filesystem error occurred.",
        code: str = "FILESYSTEM_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class PathValidationError(FilesystemError):
    """Path format or normalization failed."""

    def __init__(
        self,
        message: str = "Path validation failed.",
        code: str = "INVALID_PATH",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class PathTraversalError(FilesystemError):
    """Attempted path traversal (`../`) detected."""

    def __init__(
        self,
        message: str = "Path traversal violation detected.",
        code: str = "PATH_TRAVERSAL",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 403,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ProtectedPathError(FilesystemError):
    """Attempted access to protected system path."""

    def __init__(
        self,
        message: str = "Target path is protected by system security policy.",
        code: str = "PROTECTED_PATH",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 403,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class SandboxViolationError(FilesystemError):
    """Attempted path access outside allowed root directories."""

    def __init__(
        self,
        message: str = "Path is outside allowed sandbox root directories.",
        code: str = "SANDBOX_VIOLATION",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 403,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class SymlinkEscapeError(FilesystemError):
    """Symlink target resolves outside allowed sandbox root."""

    def __init__(
        self,
        message: str = "Symlink target resolves outside allowed sandbox root.",
        code: str = "SYMLINK_ESCAPE",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 403,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class FilesystemNotFoundError(FilesystemError):
    """Target file or directory path was not found."""

    def __init__(
        self,
        message: str = "Target file or directory not found.",
        code: str = "PATH_NOT_FOUND",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 404,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class FileAlreadyExistsError(FilesystemError):
    """Destination or target file already exists."""

    def __init__(
        self,
        message: str = "File or directory already exists.",
        code: str = "FILE_EXISTS",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 409,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class FilesystemPermissionError(FilesystemError):
    """Lacks valid authorization token from Module 15."""

    def __init__(
        self,
        message: str = "Action lacks valid Module 15 security authorization.",
        code: str = "FILESYSTEM_PERMISSION_DENIED",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 403,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class FileTooLargeError(FilesystemError):
    """File size exceeds configured read or write limit."""

    def __init__(
        self,
        message: str = "File size exceeds safety limit.",
        code: str = "FILE_TOO_LARGE",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 413,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class SearchLimitError(FilesystemError):
    """Search depth or result count limit exceeded."""

    def __init__(
        self,
        message: str = "Search limits exceeded.",
        code: str = "SEARCH_LIMIT_EXCEEDED",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class FilesystemTimeoutError(FilesystemError):
    """Filesystem operation execution timed out."""

    def __init__(
        self,
        message: str = "Filesystem operation timed out.",
        code: str = "OPERATION_TIMEOUT",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 408,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class FilesystemBackendUnavailableError(FilesystemError):
    """Filesystem backend is unavailable."""

    def __init__(
        self,
        message: str = "Filesystem backend is unavailable.",
        code: str = "BACKEND_UNAVAILABLE",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 503,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class InvalidFilesystemOperationError(FilesystemError):
    """Filesystem operation parameter or target is invalid."""

    def __init__(
        self,
        message: str = "Invalid filesystem operation.",
        code: str = "INVALID_OPERATION",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)
