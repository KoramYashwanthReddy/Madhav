"""Global dependency injection container for Module 18 — Terminal Agent."""

from max.config.settings import get_settings
from max.terminal.backends.base import TerminalBackend
from max.terminal.backends.mock import MockTerminalBackend
from max.terminal.backends.windows import WindowsTerminalBackend
from max.terminal.domain.enums import TerminalShell
from max.terminal.repositories.repositories import (
    CommandExecutionRepository,
    TerminalSessionRepository,
    TerminalTraceRepository,
)
from max.terminal.security.command_policy import CommandPolicyService
from max.terminal.services.terminal_service import TerminalService
from max.security.container import get_security_container
from max.security.services.gate import PermissionGate


class TerminalContainer:
    """Dependency injection container for the Terminal Agent subsystem."""

    def __init__(
        self,
        use_mock_backend: bool | None = None,
        custom_backend: TerminalBackend | None = None,
    ) -> None:
        cfg = get_settings().terminal
        self.settings = cfg

        # Policy service — no external dependencies
        self.policy_service = CommandPolicyService()

        # Backend selection
        if custom_backend is not None:
            self.backend: TerminalBackend = custom_backend
        elif use_mock_backend or (use_mock_backend is None and cfg.dry_run):
            self.backend = MockTerminalBackend()
        else:
            # Default: Windows backend; WSL could be selected via settings
            self.backend = WindowsTerminalBackend()

        # Repositories
        self.execution_repo = CommandExecutionRepository()
        self.session_repo = TerminalSessionRepository()
        self.trace_repo = TerminalTraceRepository()

        # Module 15 Permission Gate integration
        self.permission_gate: PermissionGate | None = None
        try:
            sec_container = get_security_container()
            self.permission_gate = sec_container.gate
        except Exception:
            self.permission_gate = None

        # Primary service facade
        self.terminal_service = TerminalService(
            settings=cfg,
            policy_service=self.policy_service,
            backend=self.backend,
            execution_repo=self.execution_repo,
            session_repo=self.session_repo,
            trace_repo=self.trace_repo,
            permission_gate=self.permission_gate,
        )


_container_instance: TerminalContainer | None = None


def get_terminal_container(
    use_mock_backend: bool | None = None,
) -> TerminalContainer:
    """Retrieve or initialize the global TerminalContainer instance."""
    global _container_instance
    if _container_instance is None:
        _container_instance = TerminalContainer(use_mock_backend=use_mock_backend)
    return _container_instance


def reset_terminal_container() -> None:
    """Reset the global TerminalContainer instance (used for test isolation)."""
    global _container_instance
    _container_instance = None
