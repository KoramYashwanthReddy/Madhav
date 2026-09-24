"""Filesystem observation service for read-only filesystem operations."""

from max.filesystem.backends.base import FilesystemBackend
from max.filesystem.domain.enums import FileEncoding
from max.filesystem.domain.models import (
    CompareResult,
    DirectoryListing,
    FileMetadata,
    FileReadResult,
    HashResult,
    PathReference,
    SearchFilter,
    SearchResponseData,
)


class FilesystemObservationService:
    """Handles read-only filesystem observations through the filesystem backend."""

    def __init__(self, backend: FilesystemBackend) -> None:
        self._backend = backend

    def exists(self, path: PathReference | str) -> bool:
        """Check if a file or directory exists."""
        target = path.resolved_path if isinstance(path, PathReference) else path
        return self._backend.exists(target)

    def stat(self, path: PathReference | str) -> FileMetadata:
        """Get file or directory metadata."""
        target = path.resolved_path if isinstance(path, PathReference) else path
        return self._backend.stat(target)

    def list_directory(self, path: PathReference | str, limit: int = 100) -> DirectoryListing:
        """List directory contents."""
        target = path.resolved_path if isinstance(path, PathReference) else path
        return self._backend.list_directory(target, limit=limit)

    def read_file(
        self,
        path: PathReference | str,
        encoding: FileEncoding = FileEncoding.UTF_8,
        max_bytes: int = 10_485_760,
        offset: int = 0,
    ) -> FileReadResult:
        """Read text or binary file content safely with size limits."""
        target = path.resolved_path if isinstance(path, PathReference) else path
        return self._backend.read_file(
            path=target,
            encoding=encoding,
            max_bytes=max_bytes,
            offset=offset,
        )

    def search(self, root_path: PathReference | str, search_filter: SearchFilter) -> SearchResponseData:
        """Search filesystem recursively within configured limits."""
        target = root_path.resolved_path if isinstance(root_path, PathReference) else root_path
        return self._backend.search(root_path=target, search_filter=search_filter)

    def hash_file(
        self, path: PathReference | str, algorithm: str = "SHA-256"
    ) -> HashResult:
        """Calculate file hash (SHA-256 by default)."""
        target = path.resolved_path if isinstance(path, PathReference) else path
        return self._backend.hash_file(path=target, algorithm=algorithm)

    def compare_files(
        self, path1: PathReference | str, path2: PathReference | str
    ) -> CompareResult:
        """Compare two files by size, hash, and content."""
        target1 = path1.resolved_path if isinstance(path1, PathReference) else path1
        target2 = path2.resolved_path if isinstance(path2, PathReference) else path2
        return self._backend.compare_files(path_a=target1, path_b=target2)
