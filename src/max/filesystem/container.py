"""Global container and dependency resolution for Module 17 — Filesystem Agent."""


from max.config.settings import get_settings
from max.filesystem.backends.base import FilesystemBackend
from max.filesystem.backends.local import LocalFilesystemBackend
from max.filesystem.backends.mock import MockFilesystemBackend
from max.filesystem.repositories.operation_repository import FileOperationRepository
from max.filesystem.repositories.trace_repository import FilesystemTraceRepository
from max.filesystem.security.path_security import PathSecurityService
from max.filesystem.services.filesystem_service import FilesystemService
from max.security.container import get_security_container
from max.security.services.gate import PermissionGate


class FilesystemContainer:
    """Dependency injection container for the Filesystem Agent subsystem."""

    def __init__(
        self,
        use_mock_backend: bool | None = None,
        custom_backend: FilesystemBackend | None = None,
    ) -> None:
        cfg = get_settings().filesystem
        self.settings = cfg

        # Security validation service
        self.path_security = PathSecurityService(settings=cfg)

        # Backend selection
        if custom_backend is not None:
            self.backend = custom_backend
        elif use_mock_backend or (use_mock_backend is None and cfg.dry_run):
            self.backend = MockFilesystemBackend()
        else:
            self.backend = LocalFilesystemBackend()

        # Repositories
        self.operation_repo = FileOperationRepository()
        self.trace_repo = FilesystemTraceRepository()

        # Module 15 Permission Gate integration
        self.permission_gate: PermissionGate | None = None
        try:
            sec_container = get_security_container()
            self.permission_gate = sec_container.gate
        except Exception:
            self.permission_gate = None

        # Main facade service
        self.filesystem_service = FilesystemService(
            settings=cfg,
            path_security=self.path_security,
            backend=self.backend,
            operation_repo=self.operation_repo,
            trace_repo=self.trace_repo,
            permission_gate=self.permission_gate,
        )


_container_instance: FilesystemContainer | None = None


def get_filesystem_container(
    use_mock_backend: bool | None = None,
) -> FilesystemContainer:
    """Retrieve or initialize the global FilesystemContainer instance."""
    global _container_instance
    if _container_instance is None:
        _container_instance = FilesystemContainer(use_mock_backend=use_mock_backend)
    return _container_instance


def reset_filesystem_container() -> None:
    """Reset the global FilesystemContainer instance (used for test isolation)."""
    global _container_instance
    _container_instance = None
