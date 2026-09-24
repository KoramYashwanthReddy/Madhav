"""Deterministic in-memory MockFilesystemBackend for safe testing and simulation."""

import hashlib
import threading
from datetime import UTC, datetime
from typing import Any

from max.filesystem.backends.base import FilesystemBackend
from max.filesystem.domain.enums import FileEncoding, FileType
from max.filesystem.domain.exceptions import (
    FileAlreadyExistsError,
    FilesystemError,
    FilesystemNotFoundError,
    InvalidFilesystemOperationError,
)
from max.filesystem.domain.models import (
    CompareResult,
    DirectoryListing,
    DirectoryMetadata,
    FileMetadata,
    FileReadResult,
    FileSystemEntry,
    FileWriteResult,
    HashResult,
    SearchFilter,
    SearchResponseData,
    SearchResultEntry,
)


class MockFilesystemNode:
    """In-memory node representing a file or directory."""

    def __init__(
        self,
        name: str,
        path: str,
        is_directory: bool = False,
        content: str | bytes = "",
        is_symlink: bool = False,
        symlink_target: str | None = None,
    ) -> None:
        self.name = name
        self.path = path
        self.is_directory = is_directory
        self.content: bytes = content if isinstance(content, bytes) else content.encode("utf-8")
        self.is_symlink = is_symlink
        self.symlink_target = symlink_target
        self.created_at = datetime.now(UTC)
        self.modified_at = datetime.now(UTC)
        self.children: dict[str, MockFilesystemNode] = {}


class MockFilesystemBackend(FilesystemBackend):
    """Deterministic in-memory mock filesystem backend."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.root = MockFilesystemNode(name="", path="/mock", is_directory=True)
        self.recorded_operations: list[dict[str, Any]] = []

        # Pre-populate safe default virtual directory structure
        self.create_directory("/mock/docs")
        self.write_file("/mock/docs/sample.txt", content="Hello Max Virtual Filesystem!")

    def is_available(self) -> bool:
        return True

    def exists(self, path: str) -> bool:
        with self._lock:
            return self._find_node(path) is not None

    def stat(self, path: str) -> FileMetadata:
        with self._lock:
            node = self._find_node(path)
            if not node:
                raise FilesystemNotFoundError(f"Mock path '{path}' not found.")

            f_type = FileType.DIRECTORY if node.is_directory else (FileType.SYMLINK if node.is_symlink else FileType.REGULAR_FILE)
            ext = node.name.split(".")[-1] if "." in node.name and not node.is_directory else ""

            return FileMetadata(
                name=node.name,
                path=node.path,
                type=f_type,
                size=len(node.content) if not node.is_directory else 0,
                created_at=node.created_at,
                modified_at=node.modified_at,
                is_symlink=node.is_symlink,
                symlink_target=node.symlink_target,
                extension=ext,
            )

    def list_directory(self, path: str, limit: int = 100) -> DirectoryListing:
        with self._lock:
            node = self._find_node(path)
            if not node:
                raise FilesystemNotFoundError(f"Mock directory '{path}' not found.")
            if not node.is_directory:
                raise InvalidFilesystemOperationError(f"Mock path '{path}' is not a directory.")

            entries: list[FileSystemEntry] = []
            child_list = list(node.children.values())
            truncated = len(child_list) > limit

            for child in child_list[:limit]:
                f_type = FileType.DIRECTORY if child.is_directory else (FileType.SYMLINK if child.is_symlink else FileType.REGULAR_FILE)
                entries.append(
                    FileSystemEntry(
                        name=child.name,
                        path=child.path,
                        type=f_type,
                        size=len(child.content) if not child.is_directory else 0,
                        modified_at=child.modified_at,
                        is_symlink=child.is_symlink,
                    )
                )

            return DirectoryListing(
                path=node.path,
                entries=entries,
                count=len(entries),
                truncated=truncated,
                limit=limit,
            )

    def read_file(
        self,
        path: str,
        encoding: FileEncoding = FileEncoding.UTF_8,
        max_bytes: int = 10485760,
        offset: int = 0,
    ) -> FileReadResult:
        with self._lock:
            node = self._find_node(path)
            if not node:
                raise FilesystemNotFoundError(f"Mock file '{path}' not found.")
            if node.is_directory:
                raise InvalidFilesystemOperationError(f"Mock path '{path}' is a directory.")

            file_size = len(node.content)
            raw = node.content[offset : offset + max_bytes + 1]
            bytes_read = min(len(raw), max_bytes)
            truncated = len(raw) > max_bytes
            raw_chunk = raw[:max_bytes]

            self.recorded_operations.append({"op": "READ_FILE", "path": path})

            if encoding == FileEncoding.BINARY:
                return FileReadResult(
                    path=node.path,
                    content=raw_chunk.hex(),
                    encoding=FileEncoding.BINARY,
                    size=file_size,
                    bytes_read=bytes_read,
                    truncated=truncated,
                    binary=True,
                )

            try:
                text = raw_chunk.decode("utf-8")
                return FileReadResult(
                    path=node.path,
                    content=text,
                    encoding=encoding,
                    size=file_size,
                    bytes_read=bytes_read,
                    truncated=truncated,
                    binary=False,
                )
            except UnicodeDecodeError:
                return FileReadResult(
                    path=node.path,
                    content=raw_chunk.hex(),
                    encoding=FileEncoding.BINARY,
                    size=file_size,
                    bytes_read=bytes_read,
                    truncated=truncated,
                    binary=True,
                )

    def write_file(
        self,
        path: str,
        content: str | bytes,
        encoding: FileEncoding = FileEncoding.UTF_8,
        overwrite: bool = False,
        create_parents: bool = True,
    ) -> FileWriteResult:
        with self._lock:
            existing = self._find_node(path)
            if existing and not overwrite:
                raise FileAlreadyExistsError(f"Mock file '{path}' already exists.")

            raw_bytes = content if isinstance(content, bytes) else content.encode("utf-8")
            norm_path = self._normalize(path)
            parts = [p for p in norm_path.split("/") if p]
            if not parts:
                raise InvalidFilesystemOperationError("Invalid target path.")

            parent_node = self.root
            for p in parts[:-1]:
                if p not in parent_node.children:
                    if create_parents:
                        new_dir = MockFilesystemNode(name=p, path=parent_node.path + "/" + p, is_directory=True)
                        parent_node.children[p] = new_dir
                        parent_node = new_dir
                    else:
                        raise FilesystemNotFoundError(f"Parent directory for '{path}' does not exist.")
                else:
                    parent_node = parent_node.children[p]

            filename = parts[-1]
            new_node = MockFilesystemNode(
                name=filename,
                path=norm_path,
                is_directory=False,
                content=raw_bytes,
            )
            parent_node.children[filename] = new_node

            f_hash = hashlib.sha256(raw_bytes).hexdigest()
            self.recorded_operations.append({"op": "WRITE_FILE", "path": norm_path, "bytes": len(raw_bytes)})

            return FileWriteResult(
                path=norm_path,
                bytes_written=len(raw_bytes),
                created=existing is None,
                overwritten=existing is not None,
                hash=f_hash,
            )

    def append_file(
        self,
        path: str,
        content: str | bytes,
        encoding: FileEncoding = FileEncoding.UTF_8,
    ) -> FileWriteResult:
        with self._lock:
            node = self._find_node(path)
            if not node or node.is_directory:
                raise FilesystemNotFoundError(f"Mock file '{path}' not found for append.")

            raw_bytes = content if isinstance(content, bytes) else content.encode("utf-8")
            node.content += raw_bytes
            node.modified_at = datetime.now(UTC)

            new_hash = hashlib.sha256(node.content).hexdigest()
            self.recorded_operations.append({"op": "APPEND_FILE", "path": path, "bytes": len(raw_bytes)})

            return FileWriteResult(
                path=node.path,
                bytes_written=len(raw_bytes),
                created=False,
                overwritten=False,
                hash=new_hash,
            )

    def create_file(self, path: str) -> FileWriteResult:
        return self.write_file(path=path, content="", overwrite=False, create_parents=True)

    def create_directory(self, path: str, create_parents: bool = True) -> DirectoryMetadata:
        with self._lock:
            norm_path = self._normalize(path)
            parts = [p for p in norm_path.split("/") if p]
            parent_node = self.root

            for p in parts:
                if p not in parent_node.children:
                    new_dir = MockFilesystemNode(name=p, path=parent_node.path + "/" + p, is_directory=True)
                    parent_node.children[p] = new_dir
                    parent_node = new_dir
                else:
                    parent_node = parent_node.children[p]

            self.recorded_operations.append({"op": "CREATE_DIRECTORY", "path": norm_path})
            return DirectoryMetadata(
                name=parent_node.name,
                path=parent_node.path,
                total_files=len([c for c in parent_node.children.values() if not c.is_directory]),
                total_subdirectories=len([c for c in parent_node.children.values() if c.is_directory]),
                created_at=parent_node.created_at,
                modified_at=parent_node.modified_at,
            )

    def copy_file(self, source: str, destination: str, overwrite: bool = False) -> FileWriteResult:
        with self._lock:
            src_node = self._find_node(source)
            if not src_node or src_node.is_directory:
                raise FilesystemNotFoundError(f"Mock source file '{source}' not found.")

            res = self.write_file(
                path=destination,
                content=src_node.content,
                overwrite=overwrite,
                create_parents=True,
            )
            self.recorded_operations.append({"op": "COPY_FILE", "source": source, "destination": destination})
            return res

    def copy_directory(
        self, source: str, destination: str, overwrite: bool = False
    ) -> DirectoryMetadata:
        with self._lock:
            src_node = self._find_node(source)
            if not src_node or not src_node.is_directory:
                raise FilesystemNotFoundError(f"Mock source directory '{source}' not found.")

            dir_meta = self.create_directory(destination)
            # Copy child nodes recursively
            for child in src_node.children.values():
                child_dest = destination + "/" + child.name
                if child.is_directory:
                    self.copy_directory(child.path, child_dest, overwrite=overwrite)
                else:
                    self.copy_file(child.path, child_dest, overwrite=overwrite)

            return dir_meta

    def move(self, source: str, destination: str, overwrite: bool = False) -> FileWriteResult:
        with self._lock:
            src_node = self._find_node(source)
            if not src_node:
                raise FilesystemNotFoundError(f"Mock source '{source}' not found.")

            if src_node.is_directory:
                self.copy_directory(source, destination, overwrite=overwrite)
                self.delete_directory(source, recursive=True)
                return FileWriteResult(
                    path=destination, bytes_written=0, created=True, overwritten=False
                )
            else:
                res = self.copy_file(source, destination, overwrite=overwrite)
                self.delete_file(source)
                self.recorded_operations.append({"op": "MOVE", "source": source, "destination": destination})
                return res

    def rename(self, source: str, new_name: str) -> FileWriteResult:
        norm_source = self._normalize(source)
        parent_path = "/".join(norm_source.split("/")[:-1])
        dest_path = parent_path + "/" + new_name if parent_path else "/" + new_name
        return self.move(source, dest_path, overwrite=False)

    def delete_file(self, path: str) -> bool:
        with self._lock:
            norm_path = self._normalize(path)
            parts = [p for p in norm_path.split("/") if p]
            if not parts:
                return False

            parent_path = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/mock"
            parent_node = self._find_node(parent_path)
            target_name = parts[-1]

            if parent_node and target_name in parent_node.children:
                del parent_node.children[target_name]
                self.recorded_operations.append({"op": "DELETE_FILE", "path": path})
                return True

            raise FilesystemNotFoundError(f"Mock file '{path}' not found for deletion.")

    def delete_directory(self, path: str, recursive: bool = False) -> bool:
        with self._lock:
            node = self._find_node(path)
            if not node or not node.is_directory:
                raise FilesystemNotFoundError(f"Mock directory '{path}' not found.")
            if node.children and not recursive:
                raise FilesystemError(f"Mock directory '{path}' is not empty and recursive is False.")

            return self.delete_file(path)

    def search(self, root_path: str, search_filter: SearchFilter) -> SearchResponseData:
        with self._lock:
            root_node = self._find_node(root_path)
            if not root_node or not root_node.is_directory:
                raise FilesystemNotFoundError(f"Search root '{root_path}' not found.")

            results: list[SearchResultEntry] = []
            stack = [(root_node, 0)]
            truncated = False

            while stack:
                curr, depth = stack.pop()
                if depth > search_filter.max_depth:
                    continue

                for child in curr.children.values():
                    matches = True
                    if search_filter.query and search_filter.query.lower() not in child.name.lower():
                        matches = False
                    if matches and search_filter.extension:
                        if not child.name.endswith(search_filter.extension):
                            matches = False

                    if matches:
                        f_type = FileType.DIRECTORY if child.is_directory else FileType.REGULAR_FILE
                        results.append(
                            SearchResultEntry(
                                path=child.path,
                                type=f_type,
                                size=len(child.content) if not child.is_directory else 0,
                                modified_at=child.modified_at,
                            )
                        )

                    if len(results) >= search_filter.max_results:
                        truncated = True
                        break

                    if child.is_directory:
                        stack.append((child, depth + 1))

                if truncated:
                    break

            return SearchResponseData(
                query=search_filter.query,
                root_path=root_node.path,
                results=results,
                count=len(results),
                truncated=truncated,
                limit_reached=truncated,
                duration_seconds=0.01,
            )

    def hash_file(self, path: str, algorithm: str = "SHA-256") -> HashResult:
        with self._lock:
            node = self._find_node(path)
            if not node or node.is_directory:
                raise FilesystemNotFoundError(f"Mock file '{path}' not found for hash.")

            h = hashlib.sha256(node.content).hexdigest()
            return HashResult(path=node.path, algorithm=algorithm.upper(), hash_value=h, size=len(node.content))

    def compare_files(self, path_a: str, path_b: str) -> CompareResult:
        with self._lock:
            node_a = self._find_node(path_a)
            node_b = self._find_node(path_b)
            if not node_a or not node_b:
                raise FilesystemNotFoundError("One or both mock files for comparison not found.")

            match = node_a.content == node_b.content
            return CompareResult(
                path_a=node_a.path,
                path_b=node_b.path,
                identical=match,
                size_match=len(node_a.content) == len(node_b.content),
                hash_match=match,
                difference_summary="Files are identical" if match else "Content differs",
            )

    def _normalize(self, path: str) -> str:
        clean = path.replace("\\", "/").rstrip("/")
        if not clean.startswith("/"):
            clean = "/mock/" + clean
        return clean

    def _find_node(self, path: str) -> MockFilesystemNode | None:
        norm = self._normalize(path)
        parts = [p for p in norm.split("/") if p]
        curr = self.root

        for p in parts:
            if curr and p in curr.children:
                curr = curr.children[p]
            elif curr and curr.name == p:
                continue
            else:
                return None
        return curr
