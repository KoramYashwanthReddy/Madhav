"""Dependency container for Module 16 — Computer Control."""

import logging

from max.computer.backends.base import ComputerControlBackend
from max.computer.backends.mock import MockComputerControlBackend
from max.computer.backends.platform_detector import PlatformDetector
from max.computer.backends.windows import WindowsComputerControlBackend
from max.computer.domain.enums import PlatformType
from max.computer.repositories.action_repository import ComputerActionRepository
from max.computer.repositories.sequence_repository import ComputerSequenceRepository
from max.computer.repositories.trace_repository import ComputerTraceRepository
from max.computer.services.action_service import ComputerActionService
from max.computer.services.control_service import ComputerControlService
from max.computer.services.observation_service import ComputerObservationService
from max.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class ComputerContainer:
    """Singleton container managing repositories, backends, and services for computer control."""

    def __init__(
        self,
        settings: Settings | None = None,
        backend_override: ComputerControlBackend | None = None,
    ) -> None:
        self.settings = settings or get_settings()

        # Repositories
        self.action_repo = ComputerActionRepository()
        self.sequence_repo = ComputerSequenceRepository()
        self.trace_repo = ComputerTraceRepository()

        # Backend Selection
        if backend_override:
            self.backend = backend_override
        else:
            p_cfg = self.settings.computer_control
            platform = PlatformDetector.detect()
            if p_cfg.enabled and platform == PlatformType.WINDOWS:
                win_backend = WindowsComputerControlBackend()
                if win_backend.is_available():
                    self.backend = win_backend
                else:
                    logger.warning("Windows backend requested but native dependencies unavailable; falling back to Mock backend")
                    self.backend = MockComputerControlBackend()
            else:
                self.backend = MockComputerControlBackend()

        # Services
        self.observation_service = ComputerObservationService(backend=self.backend)
        self.action_service = ComputerActionService(
            backend=self.backend,
            action_repository=self.action_repo,
            sequence_repository=self.sequence_repo,
            trace_repository=self.trace_repo,
            settings=self.settings,
        )
        self.control_service = ComputerControlService(
            backend=self.backend,
            observation_service=self.observation_service,
            action_service=self.action_service,
            settings=self.settings,
        )


_computer_container: ComputerContainer | None = None


def get_computer_container() -> ComputerContainer:
    """Retrieve global ComputerContainer singleton instance."""
    global _computer_container
    if _computer_container is None:
        _computer_container = ComputerContainer()
    return _computer_container


def reset_computer_container() -> None:
    """Reset global ComputerContainer instance (useful for test isolation)."""
    global _computer_container
    _computer_container = None
