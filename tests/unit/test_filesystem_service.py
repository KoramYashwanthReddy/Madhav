"""Unit tests for FilesystemService facade, Module 15 authorization, and dry-run mode."""

import tempfile
from pathlib import Path

import pytest

from max.config.sections import FilesystemSettings
from max.filesystem.backends.mock import MockFilesystemBackend
from max.filesystem.domain.action import FileOperationRequest
from max.filesystem.domain.enums import (
    FileFailureReason,
    FileOperationStatus,
    FileOperationType,
)
from max.filesystem.repositories.operation_repository import FileOperationRepository
from max.filesystem.repositories.trace_repository import FilesystemTraceRepository
from max.filesystem.security.path_security import PathSecurityService
from max.filesystem.services.filesystem_service import FilesystemService


@pytest.fixture
def service_setup():
    """Setup FilesystemService with MockBackend and isolated allowed root."""
    with tempfile.TemporaryDirectory() as temp_dir:
        root_path = Path(temp_dir).resolve()
        settings = FilesystemSettings(
            enabled=True,
            dry_run=False,
            allowed_roots=[root_path],
        )
        path_sec = PathSecurityService(settings=settings)
        backend = MockFilesystemBackend()
        op_repo = FileOperationRepository()
        trace_repo = FilesystemTraceRepository()

        service = FilesystemService(
            settings=settings,
            path_security=path_sec,
            backend=backend,
            operation_repo=op_repo,
            trace_repo=trace_repo,
            permission_gate=None,  # Disabled for pure service unit tests
        )
        yield service, root_path, trace_repo, op_repo


def test_service_execute_write_and_read(service_setup):
    """Test write and read operations through FilesystemService."""
    service, root_path, trace_repo, op_repo = service_setup
    file_path = str(root_path / "note.txt")

    # 1. Write file
    write_req = FileOperationRequest(
        operation_id="op_write_1",
        operation_type=FileOperationType.WRITE_FILE,
        source=file_path,
        parameters={"content": "Filesystem Agent Unit Test"},
    )
    write_res = service.execute_operation(write_req)
    assert write_res.status == FileOperationStatus.COMPLETED
    assert write_res.observed_state["bytes_written"] > 0

    # 2. Read file
    read_req = FileOperationRequest(
        operation_id="op_read_1",
        operation_type=FileOperationType.READ_FILE,
        source=file_path,
    )
    read_res = service.execute_operation(read_req)
    assert read_res.status == FileOperationStatus.COMPLETED
    assert read_res.observed_state["content"] == "Filesystem Agent Unit Test"

    # 3. Verify trace repository events
    traces = trace_repo.list_events()
    assert len(traces) > 0


def test_dry_run_mode(service_setup):
    """Test dry_run mode returns SIMULATED without backend state changes."""
    service, root_path, _, _ = service_setup
    file_path = str(root_path / "dry_run.txt")

    req = FileOperationRequest(
        operation_id="op_dry_1",
        operation_type=FileOperationType.WRITE_FILE,
        source=file_path,
        parameters={"content": "Should not write", "dry_run": True},
    )
    res = service.execute_operation(req)
    assert res.status == FileOperationStatus.SIMULATED
    assert res.observed_state["simulated"] is True


def test_subsystem_disabled(service_setup):
    """Test disabled filesystem agent rejects requests."""
    service, root_path, _, _ = service_setup
    service._settings.enabled = False

    req = FileOperationRequest(
        operation_id="op_dis_1",
        operation_type=FileOperationType.EXISTS,
        source=str(root_path / "any.txt"),
    )
    res = service.execute_operation(req)
    assert res.status == FileOperationStatus.FAILED
    assert res.observed_state["error_reason"] == FileFailureReason.OS_ERROR.value
