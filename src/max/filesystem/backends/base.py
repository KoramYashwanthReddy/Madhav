"""Abstract base class interface for FilesystemBackend implementations."""

from abc import ABC, abstractmethod

from max.filesystem.domain.enums import FileEncoding
from max.filesystem.domain.models import (
    CompareResult,
    DirectoryListing,
    DirectoryMetadata,
    FileMetadata,
    FileReadResult,
    FileWriteResult,
    HashResult,
    SearchFilter,
    SearchResponseData,
)


class FilesystemBackend(ABC):
    """Abstract interface defining low-level filesystem operations."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if filesystem backend is operational."""
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if target path exists."""
        pass

    @abstractmethod
    def stat(self, path: str) -> FileMetadata:
        """Get file or directory metadata stat info."""
        pass

    @abstractmethod
    def list_directory(self, path: str, limit: int = 100) -> DirectoryListing:
        """List contents of target directory."""
        pass

    @abstractmethod
    def read_file(
        self,
        path: str,
        encoding: FileEncoding = FileEncoding.UTF_8,
        max_bytes: int = 10485760,
        offset: int = 0,
    ) -> FileReadResult:
        """Read file contents into memory up to max_bytes."""
        pass

    @abstractmethod
    def write_file(
        self,
        path: str,
        content: str | bytes,
        encoding: FileEncoding = FileEncoding.UTF_8,
        overwrite: bool = False,
        create_parents: bool = True,
    ) -> FileWriteResult:
        """Write content to target file (atomic write where supported)."""
        pass

    @abstractmethod
    def append_file(
        self,
        path: str,
        content: str | bytes,
        encoding: FileEncoding = FileEncoding.UTF_8,
    ) -> FileWriteResult:
        """Append content to end of existing file."""
        pass

    @abstractmethod
    def create_file(self, path: str) -> FileWriteResult:
        """Create empty file if not existing."""
        pass

    @abstractmethod
    def create_directory(self, path: str, create_parents: bool = True) -> DirectoryMetadata:
        """Create new directory."""
        pass

    @abstractmethod
    def copy_file(self, source: str, destination: str, overwrite: bool = False) -> FileWriteResult:
        """Copy single file from source to destination."""
        pass

    @abstractmethod
    def copy_directory(
        self, source: str, destination: str, overwrite: bool = False
    ) -> DirectoryMetadata:
        """Copy directory recursively from source to destination."""
        pass

    @abstractmethod
    def move(self, source: str, destination: str, overwrite: bool = False) -> FileWriteResult:
        """Move file or directory from source to destination."""
        pass

    @abstractmethod
    def rename(self, source: str, new_name: str) -> FileWriteResult:
        """Rename file or directory in place."""
        pass

    @abstractmethod
    def delete_file(self, path: str) -> bool:
        """Delete single file."""
        pass

    @abstractmethod
    def delete_directory(self, path: str, recursive: bool = False) -> bool:
        """Delete directory (optionally recursive)."""
        pass

    @abstractmethod
    def search(self, root_path: str, search_filter: SearchFilter) -> SearchResponseData:
        """Search directory contents using specified criteria."""
        pass

    @abstractmethod
    def hash_file(self, path: str, algorithm: str = "SHA-256") -> HashResult:
        """Calculate cryptographic hash of file content."""
        pass

    @abstractmethod
    def compare_files(self, path_a: str, path_b: str) -> CompareResult:
        """Compare content and metadata of two files."""
        pass
