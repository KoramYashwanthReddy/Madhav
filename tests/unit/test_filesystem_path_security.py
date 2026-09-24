"""Unit tests for PathSecurityService security checks and path validations."""

import tempfile
from pathlib import Path

import pytest

from max.config.sections import FilesystemSettings
from max.filesystem.domain.exceptions import (
    PathTraversalError,
    ProtectedPathError,
    SandboxViolationError,
)
from max.filesystem.security.path_security import PathSecurityService


@pytest.fixture
def temp_sandbox_env():
    """Create isolated temporary directories representing allowed and blocked roots."""
    with tempfile.TemporaryDirectory() as allowed_dir, tempfile.TemporaryDirectory() as blocked_dir:
        allowed_path = Path(allowed_dir).resolve()
        blocked_path = Path(blocked_dir).resolve()

        settings = FilesystemSettings(
            allowed_roots=[allowed_path],
            blocked_roots=[blocked_path],
        )
        service = PathSecurityService(settings=settings)
        yield service, allowed_path, blocked_path


def test_allowed_root_success(temp_sandbox_env):
    """Test valid path inside allowed root succeeds."""
    service, allowed_path, _ = temp_sandbox_env
    valid_file = allowed_path / "project" / "file.txt"

    ref = service.verify_path_access(str(valid_file))
    assert ref.resolved_path == str(valid_file.resolve())


def test_path_traversal_blocked(temp_sandbox_env):
    """Test path traversal with ../ outside allowed root is blocked."""
    service, allowed_path, _ = temp_sandbox_env
    traversal_path = allowed_path / ".." / "outside.txt"

    with pytest.raises((PathTraversalError, SandboxViolationError)):
        service.verify_path_access(str(traversal_path))


def test_blocked_root_denied(temp_sandbox_env):
    """Test explicitly blocked root path raises SandboxViolationError."""
    service, _, blocked_path = temp_sandbox_env
    file_in_blocked = blocked_path / "forbidden.txt"

    with pytest.raises(SandboxViolationError):
        service.verify_path_access(str(file_in_blocked))


def test_protected_system_paths():
    """Test standard system paths (Windows System32, /etc) are blocked."""
    settings = FilesystemSettings()
    service = PathSecurityService(settings=settings)

    with pytest.raises(ProtectedPathError):
        service.verify_path_access("C:/Windows/System32/config/sam")

    with pytest.raises(ProtectedPathError):
        service.verify_path_access("/etc/passwd")


def test_dual_path_access_validation(temp_sandbox_env):
    """Test verification for COPY and MOVE across source and destination roots."""
    service, allowed_path, blocked_path = temp_sandbox_env
    src = allowed_path / "src.txt"
    dest = allowed_path / "dest.txt"
    blocked_dest = blocked_path / "dest.txt"

    # Both allowed -> success
    ref_src, ref_dest = service.verify_dual_path_access(str(src), str(dest))
    assert ref_src.resolved_path == str(src.resolve())
    assert ref_dest.resolved_path == str(dest.resolve())

    # Destination in blocked root -> fails
    with pytest.raises(SandboxViolationError):
        service.verify_dual_path_access(str(src), str(blocked_dest))
