"""Unit tests for Module 17 Filesystem Agent domain models, enums, and exceptions."""

from max.filesystem.domain.action import (
    FileOperation,
    FileOperationRequest,
    FileOperationResult,
)
from max.filesystem.domain.enums import (
    FileEncoding,
    FileOperationStatus,
    FileOperationType,
    FileType,
)
from max.filesystem.domain.exceptions import (
    FilesystemError,
    PathTraversalError,
    ProtectedPathError,
    SymlinkEscapeError,
)
from max.filesystem.domain.models import (
    FileMetadata,
    FileReadResult,
    PathReference,
)


def test_file_type_enums():
    """Verify file type enum values."""
    assert FileType.REGULAR_FILE.value == "REGULAR_FILE"
    assert FileType.DIRECTORY.value == "DIRECTORY"
    assert FileType.SYMLINK.value == "SYMLINK"
    assert FileType.UNKNOWN.value == "UNKNOWN"


def test_file_operation_type_enums():
    """Verify file operation type values."""
    assert FileOperationType.READ_FILE.value == "READ_FILE"
    assert FileOperationType.WRITE_FILE.value == "WRITE_FILE"
    assert FileOperationType.DELETE_FILE.value == "DELETE_FILE"
    assert FileOperationType.SEARCH.value == "SEARCH"
    assert FileOperationType.COMPARE.value == "COMPARE"


def test_path_reference_model():
    """Test PathReference domain object creation and helper properties."""
    pref = PathReference(
        original_path="foo/bar.txt",
        normalized_path="foo/bar.txt",
        resolved_path="C:/workspace/foo/bar.txt",
        is_absolute=True,
        file_type=FileType.REGULAR_FILE,
        is_symlink=False,
    )
    assert pref.original_path == "foo/bar.txt"
    assert pref.resolved_path == "C:/workspace/foo/bar.txt"
    assert pref.file_type == FileType.REGULAR_FILE


def test_file_metadata_and_read_result():
    """Test metadata and read result data structures."""
    meta = FileMetadata(
        name="test.txt",
        path="C:/tmp/test.txt",
        size=128,
        extension=".txt",
        mime_type="text/plain",
    )
    assert meta.name == "test.txt"
    assert meta.size == 128

    read_res = FileReadResult(
        path="C:/tmp/test.txt",
        content="hello world",
        encoding=FileEncoding.UTF_8,
        size=11,
        bytes_read=11,
        truncated=False,
    )
    assert read_res.content == "hello world"
    assert read_res.bytes_read == 11


def test_operation_lifecycle_model():
    """Test FileOperationRequest and FileOperation lifecycle models."""
    req = FileOperationRequest(
        operation_id="op_123",
        operation_type=FileOperationType.WRITE_FILE,
        source="C:/tmp/file.txt",
        parameters={"content": "data"},
    )
    op = FileOperation(request=req, status=FileOperationStatus.CREATED)
    assert op.status == FileOperationStatus.CREATED
    assert op.request.operation_id == "op_123"

    res = FileOperationResult(
        operation_id="op_123",
        operation_type=FileOperationType.WRITE_FILE,
        status=FileOperationStatus.COMPLETED,
        source="C:/tmp/file.txt",
        duration=0.0125,
    )
    op.status = FileOperationStatus.COMPLETED
    op.result = res
    assert op.result.status == FileOperationStatus.COMPLETED


def test_filesystem_exceptions_hierarchy():
    """Test custom exception hierarchy."""
    err = PathTraversalError("Path traversal attempted")
    assert isinstance(err, FilesystemError)

    err2 = SymlinkEscapeError("Symlink escape detected")
    assert isinstance(err2, FilesystemError)

    err3 = ProtectedPathError("Access to system path denied")
    assert isinstance(err3, FilesystemError)
