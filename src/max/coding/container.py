"""Global dependency injection container for Module 22 — Coding Agent."""

from max.config.settings import get_settings
from max.coding.repositories.repositories import (
    ChangeSetRepository,
    CodingAuditRepository,
    CodingSessionRepository,
)
from max.coding.services.coding_service import CodingService


class CodingContainer:
    """Dependency injection container for the Coding Agent subsystem."""

    def __init__(self) -> None:
        cfg = get_settings().coding_agent
        self.settings = cfg

        # Repositories
        self.session_repo = CodingSessionRepository()
        self.changeset_repo = ChangeSetRepository()
        self.audit_repo = CodingAuditRepository()

        # Master service facade
        self.service = CodingService(
            session_repo=self.session_repo,
            changeset_repo=self.changeset_repo,
            audit_repo=self.audit_repo,
        )


_container_instance: CodingContainer | None = None


def get_coding_container() -> CodingContainer:
    """Retrieve or initialize the global CodingContainer instance."""
    global _container_instance
    if _container_instance is None:
        _container_instance = CodingContainer()
    return _container_instance


def reset_coding_container() -> None:
    """Reset the global CodingContainer instance (used for test isolation)."""
    global _container_instance
    _container_instance = None
