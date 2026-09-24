"""Filesystem mutation service for state-changing filesystem operations."""

from max.filesystem.backends.base import FilesystemBackend
from max.filesystem.domain.enums import FileEncoding
from max.filesystem.domain.models import (
    DirectoryMetadata,
    FileWriteResult,
    PathReference,
)


class FilesystemMutationService:
    """Handles mutating filesystem actions through the filesystem backend."""

    def __init__(self, backend: FilesystemBackend) -> None:
        self._backend = backend

    def create_file(
        self, path: PathReference | str
    ) -> FileWriteResult:
        """Create a new empty file."""
        target = path.resolved_path if isinstance(path, PathReference) else path
        return self._backend.create_file(path=target)

    def create_directory(
        self, path: PathReference | str, parents: bool = True
    ) -> DirectoryMetadata:
        """Create a directory."""
        target = path.resolved_path if isinstance(path, PathReference) else path
        return self._backend.create_directory(path=target, create_parents=parents)

    def write_file(
        self,
        path: PathReference | str,
        content: str | bytes,
        encoding: FileEncoding = FileEncoding.UTF_8,
        overwrite: bool = True,
        create_parents: bool = True,
    ) -> FileWriteResult:
        """Write content to file (atomic write supported)."""
        target = path.resolved_path if isinstance(path, PathReference) else path
        return self._backend.write_file(
            path=target,
            content=content,
            encoding=encoding,
            overwrite=overwrite,
            create_parents=create_parents,
        )

    def append_file(
        self,
        path: PathReference | str,
        content: str | bytes,
        encoding: FileEncoding = FileEncoding.UTF_8,
    ) -> FileWriteResult:
        """Append content to file."""
        target = path.resolved_path if isinstance(path, PathReference) else path
        return self._backend.append_file(path=target, content=content, encoding=encoding)

    def copy_file(
        self, source: PathReference | str, destination: PathReference | str, overwrite: bool = False
    ) -> FileWriteResult:
        """Copy file from source to destination."""
        src_target = source.resolved_path if isinstance(source, PathReference) else source
        dest_target = destination.resolved_path if isinstance(destination, PathReference) else destination
        return self._backend.copy_file(source=src_target, destination=dest_target, overwrite=overwrite)

    def copy_directory(
        self, source: PathReference | str, destination: PathReference | str, overwrite: bool = False
    ) -> DirectoryMetadata:
        """Copy directory from source to destination."""
        src_target = source.resolved_path if isinstance(source, PathReference) else source
        dest_target = destination.resolved_path if isinstance(destination, PathReference) else destination
        return self._backend.copy_directory(source=src_target, destination=dest_target, overwrite=overwrite)

    def move(
        self, source: PathReference | str, destination: PathReference | str, overwrite: bool = False
    ) -> FileWriteResult:
        """Move or rename file/directory."""
        src_target = source.resolved_path if isinstance(source, PathReference) else source
        dest_target = destination.resolved_path if isinstance(destination, PathReference) else destination
        return self._backend.move(source=src_target, destination=dest_target, overwrite=overwrite)

    def rename(
        self, source: PathReference | str, new_name: str
    ) -> FileWriteResult:
        """Rename file or directory."""
        src_target = source.resolved_path if isinstance(source, PathReference) else source
        return self._backend.rename(source=src_target, new_name=new_name)

    def delete_file(self, path: PathReference | str) -> bool:
        """Delete a file."""
        target = path.resolved_path if isinstance(path, PathReference) else path
        return self._backend.delete_file(target)

    def delete_directory(self, path: PathReference | str, recursive: bool = False) -> bool:
        """Delete a directory (recursive deletion requires explicit flag)."""
        target = path.resolved_path if isinstance(path, PathReference) else path
        return self._backend.delete_directory(target, recursive=recursive)
