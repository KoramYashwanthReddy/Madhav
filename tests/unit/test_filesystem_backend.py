"""Unit tests for MockFilesystemBackend and LocalFilesystemBackend."""

import tempfile
from pathlib import Path

from max.filesystem.backends.local import LocalFilesystemBackend
from max.filesystem.backends.mock import MockFilesystemBackend
from max.filesystem.domain.enums import FileEncoding
from max.filesystem.domain.models import SearchFilter


def test_mock_filesystem_backend():
    """Test full file operation lifecycle in MockFilesystemBackend."""
    backend = MockFilesystemBackend()
    path_str = "/mock/test.txt"

    # 1. Initially does not exist
    assert not backend.exists(path_str)

    # 2. Write file
    w_res = backend.write_file(path_str, content="hello mock", encoding=FileEncoding.UTF_8)
    assert w_res.bytes_written == 10
    assert backend.exists(path_str)

    # 3. Read file
    r_res = backend.read_file(path_str)
    assert r_res.content == "hello mock"

    # 4. Hash file
    h_res = backend.hash_file(path_str)
    assert len(h_res.hash_value) == 64  # SHA-256 hex string length

    # 5. Delete file
    deleted = backend.delete_file(path_str)
    assert deleted
    assert not backend.exists(path_str)


def test_local_filesystem_backend():
    """Test LocalFilesystemBackend in an isolated temporary directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        backend = LocalFilesystemBackend()
        temp_path = Path(temp_dir).resolve()
        target_file = temp_path / "local_test.txt"
        file_str = str(target_file)

        # 1. Write file
        w_res = backend.write_file(file_str, content="local test data")
        assert w_res.bytes_written == 15
        assert target_file.exists()

        # 2. Read file
        r_res = backend.read_file(file_str)
        assert r_res.content == "local test data"

        # 3. Stat file
        meta = backend.stat(file_str)
        assert meta.size == 15

        # 4. Append to file
        a_res = backend.append_file(file_str, content=" extra")
        assert a_res.bytes_written == 6

        # 5. Search
        search_filter = SearchFilter(query="*.txt")
        s_res = backend.search(str(temp_path), search_filter)
        assert s_res.count == 1
        assert s_res.results[0].path == file_str

        # 6. Delete file
        deleted = backend.delete_file(file_str)
        assert deleted
        assert not target_file.exists()
