"""Local OS filesystem backend implementation using Python standard library (pathlib, shutil, os, hashlib)."""

import fnmatch
import hashlib
import mimetypes
import os
import shutil
import tempfile
import threading
from datetime import UTC, datetime
from pathlib import Path

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


class LocalFilesystemBackend(FilesystemBackend):
    """Local OS filesystem backend executing native pathlib/shutil calls."""

    def __init__(self) -> None:
        self._lock = threading.RLock()

    def is_available(self) -> bool:
        return True

    def exists(self, path: str) -> bool:
        with self._lock:
            return Path(path).exists()

    def stat(self, path: str) -> FileMetadata:
        with self._lock:
            p = Path(path)
            if not p.exists() and not p.is_symlink():
                raise FilesystemNotFoundError(f"Path '{path}' does not exist.")
            try:
                st = p.lstat() if p.is_symlink() else p.stat()
                f_type = self._resolve_file_type(p)
                ext = p.suffix.lstrip(".").lower() if f_type == FileType.REGULAR_FILE else ""
                mime, _ = mimetypes.guess_type(str(p))
                symlink_target = str(p.readlink()) if p.is_symlink() else None

                return FileMetadata(
                    name=p.name,
                    path=str(p.resolve()),
                    type=f_type,
                    size=st.st_size,
                    created_at=datetime.fromtimestamp(st.st_ctime, UTC),
                    modified_at=datetime.fromtimestamp(st.st_mtime, UTC),
                    accessed_at=datetime.fromtimestamp(st.st_atime, UTC),
                    is_symlink=p.is_symlink(),
                    symlink_target=symlink_target,
                    extension=ext,
                    mime_type=mime,
                )
            except Exception as exc:
                raise FilesystemError(f"Stat failed for '{path}': {str(exc)}") from exc

    def list_directory(self, path: str, limit: int = 100) -> DirectoryListing:
        with self._lock:
            p = Path(path)
            if not p.exists():
                raise FilesystemNotFoundError(f"Directory '{path}' not found.")
            if not p.is_dir():
                raise InvalidFilesystemOperationError(f"Path '{path}' is not a directory.")

            entries: list[FileSystemEntry] = []
            truncated = False
            try:
                child_paths = list(p.iterdir())
                if len(child_paths) > limit:
                    truncated = True
                    child_paths = child_paths[:limit]

                for child in child_paths:
                    try:
                        st = child.lstat() if child.is_symlink() else child.stat()
                        f_type = self._resolve_file_type(child)
                        entries.append(
                            FileSystemEntry(
                                name=child.name,
                                path=str(child.resolve()),
                                type=f_type,
                                size=st.st_size if f_type != FileType.DIRECTORY else 0,
                                modified_at=datetime.fromtimestamp(st.st_mtime, UTC),
                                is_symlink=child.is_symlink(),
                            )
                        )
                    except Exception:
                        continue  # Skip unreadable single entry

                return DirectoryListing(
                    path=str(p.resolve()),
                    entries=entries,
                    count=len(entries),
                    truncated=truncated,
                    limit=limit,
                )
            except Exception as exc:
                raise FilesystemError(f"Directory listing failed for '{path}': {str(exc)}") from exc

    def read_file(
        self,
        path: str,
        encoding: FileEncoding = FileEncoding.UTF_8,
        max_bytes: int = 10485760,
        offset: int = 0,
    ) -> FileReadResult:
        with self._lock:
            p = Path(path)
            if not p.exists():
                raise FilesystemNotFoundError(f"File '{path}' not found.")
            if p.is_dir():
                raise InvalidFilesystemOperationError(f"Path '{path}' is a directory.")

            file_size = p.stat().st_size
            if offset >= file_size and file_size > 0:
                return FileReadResult(
                    path=str(p.resolve()),
                    content="",
                    encoding=encoding,
                    size=file_size,
                    bytes_read=0,
                    truncated=False,
                    binary=False,
                )

            try:
                with p.open("rb") as f:
                    if offset > 0:
                        f.seek(offset)
                    raw = f.read(max_bytes + 1)

                bytes_read = min(len(raw), max_bytes)
                truncated = len(raw) > max_bytes
                raw_chunk = raw[:max_bytes]

                if encoding == FileEncoding.BINARY:
                    return FileReadResult(
                        path=str(p.resolve()),
                        content=raw_chunk.hex(),
                        encoding=FileEncoding.BINARY,
                        size=file_size,
                        bytes_read=bytes_read,
                        truncated=truncated,
                        binary=True,
                    )

                enc_name = "utf-8" if encoding == FileEncoding.UTF_8 else ("ascii" if encoding == FileEncoding.ASCII else "latin-1")
                try:
                    text_content = raw_chunk.decode(enc_name)
                    return FileReadResult(
                        path=str(p.resolve()),
                        content=text_content,
                        encoding=encoding,
                        size=file_size,
                        bytes_read=bytes_read,
                        truncated=truncated,
                        binary=False,
                    )
                except UnicodeDecodeError:
                    # Fall back to binary hex representation
                    return FileReadResult(
                        path=str(p.resolve()),
                        content=raw_chunk.hex(),
                        encoding=FileEncoding.BINARY,
                        size=file_size,
                        bytes_read=bytes_read,
                        truncated=truncated,
                        binary=True,
                    )
            except Exception as exc:
                raise FilesystemError(f"Read failed for '{path}': {str(exc)}") from exc

    def write_file(
        self,
        path: str,
        content: str | bytes,
        encoding: FileEncoding = FileEncoding.UTF_8,
        overwrite: bool = False,
        create_parents: bool = True,
    ) -> FileWriteResult:
        with self._lock:
            p = Path(path)
            existed = p.exists()

            if existed and not overwrite:
                raise FileAlreadyExistsError(f"File '{path}' already exists and overwrite is False.")

            if create_parents and not p.parent.exists():
                p.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write via temporary file in same parent directory
            tmp_fd, tmp_path_str = tempfile.mkstemp(dir=str(p.parent), prefix=".max_tmp_")
            try:
                raw_bytes = content if isinstance(content, bytes) else (
                    content.encode("utf-8" if encoding == FileEncoding.UTF_8 else "latin-1")
                )
                with os.fdopen(tmp_fd, "wb") as f:
                    f.write(raw_bytes)
                    f.flush()
                    os.fsync(f.fileno())

                # Atomic replacement
                shutil.move(tmp_path_str, str(p))
                file_hash = hashlib.sha256(raw_bytes).hexdigest()

                return FileWriteResult(
                    path=str(p.resolve()),
                    bytes_written=len(raw_bytes),
                    created=not existed,
                    overwritten=existed,
                    hash=file_hash,
                )
            except Exception as exc:
                if os.path.exists(tmp_path_str):
                    try:
                        os.remove(tmp_path_str)
                    except Exception:
                        pass
                raise FilesystemError(f"Write failed for '{path}': {str(exc)}") from exc

    def append_file(
        self,
        path: str,
        content: str | bytes,
        encoding: FileEncoding = FileEncoding.UTF_8,
    ) -> FileWriteResult:
        with self._lock:
            p = Path(path)
            if not p.exists():
                raise FilesystemNotFoundError(f"File '{path}' not found for append operation.")

            raw_bytes = content if isinstance(content, bytes) else (
                content.encode("utf-8" if encoding == FileEncoding.UTF_8 else "latin-1")
            )
            try:
                with p.open("ab") as f:
                    f.write(raw_bytes)
                    f.flush()

                new_hash = self.hash_file(str(p)).hash_value
                return FileWriteResult(
                    path=str(p.resolve()),
                    bytes_written=len(raw_bytes),
                    created=False,
                    overwritten=False,
                    hash=new_hash,
                )
            except Exception as exc:
                raise FilesystemError(f"Append failed for '{path}': {str(exc)}") from exc

    def create_file(self, path: str) -> FileWriteResult:
        return self.write_file(path=path, content="", overwrite=False, create_parents=True)

    def create_directory(self, path: str, create_parents: bool = True) -> DirectoryMetadata:
        with self._lock:
            p = Path(path)
            if p.exists() and not p.is_dir():
                raise FileAlreadyExistsError(f"Path '{path}' exists and is a file.")

            try:
                p.mkdir(parents=create_parents, exist_ok=True)
                st = p.stat()
                return DirectoryMetadata(
                    name=p.name,
                    path=str(p.resolve()),
                    total_files=0,
                    total_subdirectories=0,
                    total_size_bytes=0,
                    created_at=datetime.fromtimestamp(st.st_ctime, UTC),
                    modified_at=datetime.fromtimestamp(st.st_mtime, UTC),
                )
            except Exception as exc:
                raise FilesystemError(f"Create directory failed for '{path}': {str(exc)}") from exc

    def copy_file(self, source: str, destination: str, overwrite: bool = False) -> FileWriteResult:
        with self._lock:
            src_p = Path(source)
            dest_p = Path(destination)

            if not src_p.exists():
                raise FilesystemNotFoundError(f"Source file '{source}' not found.")
            if dest_p.exists() and not overwrite:
                raise FileAlreadyExistsError(f"Destination file '{destination}' already exists.")

            try:
                if not dest_p.parent.exists():
                    dest_p.parent.mkdir(parents=True, exist_ok=True)

                shutil.copy2(str(src_p), str(dest_p))
                st = dest_p.stat()
                f_hash = self.hash_file(str(dest_p)).hash_value

                return FileWriteResult(
                    path=str(dest_p.resolve()),
                    bytes_written=st.st_size,
                    created=not dest_p.exists(),
                    overwritten=dest_p.exists(),
                    hash=f_hash,
                )
            except Exception as exc:
                raise FilesystemError(f"Copy file failed from '{source}' to '{destination}': {str(exc)}") from exc

    def copy_directory(
        self, source: str, destination: str, overwrite: bool = False
    ) -> DirectoryMetadata:
        with self._lock:
            src_p = Path(source)
            dest_p = Path(destination)

            if not src_p.exists() or not src_p.is_dir():
                raise FilesystemNotFoundError(f"Source directory '{source}' not found.")

            try:
                shutil.copytree(str(src_p), str(dest_p), dirs_exist_ok=overwrite)
                return self._build_directory_metadata(dest_p)
            except Exception as exc:
                raise FilesystemError(f"Copy directory failed from '{source}' to '{destination}': {str(exc)}") from exc

    def move(self, source: str, destination: str, overwrite: bool = False) -> FileWriteResult:
        with self._lock:
            src_p = Path(source)
            dest_p = Path(destination)

            if not src_p.exists():
                raise FilesystemNotFoundError(f"Source path '{source}' not found.")
            if dest_p.exists() and not overwrite:
                raise FileAlreadyExistsError(f"Destination path '{destination}' exists.")

            try:
                if dest_p.exists() and overwrite:
                    if dest_p.is_dir():
                        shutil.rmtree(str(dest_p))
                    else:
                        dest_p.unlink()

                shutil.move(str(src_p), str(dest_p))
                new_size = dest_p.stat().st_size if dest_p.is_file() else 0
                return FileWriteResult(
                    path=str(dest_p.resolve()),
                    bytes_written=new_size,
                    created=True,
                    overwritten=False,
                )
            except Exception as exc:
                raise FilesystemError(f"Move failed from '{source}' to '{destination}': {str(exc)}") from exc

    def rename(self, source: str, new_name: str) -> FileWriteResult:
        with self._lock:
            src_p = Path(source)
            if not src_p.exists():
                raise FilesystemNotFoundError(f"Source path '{source}' not found.")

            dest_p = src_p.parent / new_name
            return self.move(str(src_p), str(dest_p), overwrite=False)

    def delete_file(self, path: str) -> bool:
        with self._lock:
            p = Path(path)
            if not p.exists() and not p.is_symlink():
                raise FilesystemNotFoundError(f"File '{path}' not found.")
            if p.is_dir() and not p.is_symlink():
                raise InvalidFilesystemOperationError(f"Path '{path}' is a directory; use delete_directory.")

            try:
                p.unlink()
                return True
            except Exception as exc:
                raise FilesystemError(f"Delete file failed for '{path}': {str(exc)}") from exc

    def delete_directory(self, path: str, recursive: bool = False) -> bool:
        with self._lock:
            p = Path(path)
            if not p.exists():
                raise FilesystemNotFoundError(f"Directory '{path}' not found.")
            if not p.is_dir():
                raise InvalidFilesystemOperationError(f"Path '{path}' is not a directory.")

            try:
                if recursive:
                    shutil.rmtree(str(p))
                else:
                    p.rmdir()  # Fails if non-empty
                return True
            except Exception as exc:
                raise FilesystemError(f"Delete directory failed for '{path}': {str(exc)}") from exc

    def search(self, root_path: str, search_filter: SearchFilter) -> SearchResponseData:
        with self._lock:
            t0 = datetime.now(UTC)
            p_root = Path(root_path)
            if not p_root.exists() or not p_root.is_dir():
                raise FilesystemNotFoundError(f"Search root directory '{root_path}' not found.")

            results: list[SearchResultEntry] = []
            truncated = False
            limit_reached = False

            # Bounded DFS traversal
            stack: list[tuple[Path, int]] = [(p_root, 0)]
            visited_count = 0

            while stack:
                curr_dir, depth = stack.pop()
                if depth > search_filter.max_depth:
                    limit_reached = True
                    continue

                try:
                    children = list(curr_dir.iterdir())
                except Exception:
                    continue  # Skip unreadable directory

                for child in children:
                    visited_count += 1
                    try:
                        f_type = self._resolve_file_type(child)
                        st = child.lstat() if child.is_symlink() else child.stat()
                        mtime = datetime.fromtimestamp(st.st_mtime, UTC)

                        # Match criteria check
                        matches = True

                        if search_filter.query:
                            pat = search_filter.query.lower()
                            if not fnmatch.fnmatch(child.name.lower(), pat) and pat not in child.name.lower():
                                matches = False

                        if matches and search_filter.extension:
                            ext = search_filter.extension.lstrip(".").lower()
                            if child.suffix.lstrip(".").lower() != ext:
                                matches = False

                        if matches and search_filter.file_type:
                            if f_type != search_filter.file_type:
                                matches = False

                        if matches and search_filter.min_size is not None:
                            if st.st_size < search_filter.min_size:
                                matches = False

                        if matches and search_filter.max_size is not None:
                            if st.st_size > search_filter.max_size:
                                matches = False

                        if matches and search_filter.modified_after:
                            if mtime < search_filter.modified_after:
                                matches = False

                        if matches and search_filter.modified_before:
                            if mtime > search_filter.modified_before:
                                matches = False

                        if matches:
                            results.append(
                                SearchResultEntry(
                                    path=str(child.resolve()),
                                    type=f_type,
                                    size=st.st_size,
                                    modified_at=mtime,
                                )
                            )

                        if len(results) >= search_filter.max_results:
                            truncated = True
                            limit_reached = True
                            break

                        if child.is_dir() and not child.is_symlink() and depth < search_filter.max_depth:
                            stack.append((child, depth + 1))

                    except Exception:
                        continue

                if truncated:
                    break

            duration = (datetime.now(UTC) - t0).total_seconds()
            return SearchResponseData(
                query=search_filter.query,
                root_path=str(p_root.resolve()),
                results=results,
                count=len(results),
                truncated=truncated,
                limit_reached=limit_reached,
                duration_seconds=duration,
            )

    def hash_file(self, path: str, algorithm: str = "SHA-256") -> HashResult:
        with self._lock:
            p = Path(path)
            if not p.exists() or not p.is_file():
                raise FilesystemNotFoundError(f"File '{path}' not found for hashing.")

            alg = algorithm.upper().replace("-", "")
            if alg == "SHA256":
                hasher = hashlib.sha256()
            elif alg == "SHA512":
                hasher = hashlib.sha512()
            elif alg == "MD5":
                hasher = hashlib.md5()
            else:
                raise InvalidFilesystemOperationError(f"Unsupported hash algorithm '{algorithm}'.")

            try:
                with p.open("rb") as f:
                    while chunk := f.read(8192):
                        hasher.update(chunk)

                return HashResult(
                    path=str(p.resolve()),
                    algorithm=algorithm.upper(),
                    hash_value=hasher.hexdigest(),
                    size=p.stat().st_size,
                )
            except Exception as exc:
                raise FilesystemError(f"Hash calculation failed for '{path}': {str(exc)}") from exc

    def compare_files(self, path_a: str, path_b: str) -> CompareResult:
        with self._lock:
            meta_a = self.stat(path_a)
            meta_b = self.stat(path_b)

            size_match = meta_a.size == meta_b.size
            if not size_match:
                return CompareResult(
                    path_a=meta_a.path,
                    path_b=meta_b.path,
                    identical=False,
                    size_match=False,
                    hash_match=False,
                    difference_summary=f"Size mismatch: {meta_a.size} bytes vs {meta_b.size} bytes",
                )

            hash_a = self.hash_file(path_a).hash_value
            hash_b = self.hash_file(path_b).hash_value
            hash_match = hash_a == hash_b

            return CompareResult(
                path_a=meta_a.path,
                path_b=meta_b.path,
                identical=hash_match,
                size_match=True,
                hash_match=hash_match,
                difference_summary="Files are identical" if hash_match else "File hash digests differ",
            )

    def _resolve_file_type(self, p: Path) -> FileType:
        if p.is_symlink():
            return FileType.SYMLINK
        if p.is_dir():
            return FileType.DIRECTORY
        if p.is_file():
            return FileType.REGULAR_FILE
        if p.is_socket():
            return FileType.SOCKET
        if p.is_fifo() or p.is_block_device() or p.is_char_device():
            return FileType.DEVICE
        return FileType.UNKNOWN

    def _build_directory_metadata(self, p: Path) -> DirectoryMetadata:
        st = p.stat()
        files_cnt = 0
        dirs_cnt = 0
        total_sz = 0
        try:
            for child in p.iterdir():
                if child.is_file():
                    files_cnt += 1
                    total_sz += child.stat().st_size
                elif child.is_dir():
                    dirs_cnt += 1
        except Exception:
            pass

        return DirectoryMetadata(
            name=p.name,
            path=str(p.resolve()),
            total_files=files_cnt,
            total_subdirectories=dirs_cnt,
            total_size_bytes=total_sz,
            created_at=datetime.fromtimestamp(st.st_ctime, UTC),
            modified_at=datetime.fromtimestamp(st.st_mtime, UTC),
        )
