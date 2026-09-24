"""Global dependency injection container for Module 21 — Web Intelligence."""

from max.config.settings import get_settings
from max.web_intelligence.providers.base import BaseSearchProvider
from max.web_intelligence.providers.mock import MockSearchProvider
from max.web_intelligence.repositories.repositories import (
    EvidenceRepository,
    ResearchAuditRepository,
    ResearchRepository,
    SourceRepository,
)
from max.web_intelligence.services.web_intelligence_service import WebIntelligenceService


class WebIntelligenceContainer:
    """Dependency injection container for the Web Intelligence subsystem."""

    def __init__(
        self,
        custom_provider: BaseSearchProvider | None = None,
    ) -> None:
        cfg = get_settings().web_intelligence
        self.settings = cfg

        # Repositories
        self.research_repo = ResearchRepository()
        self.source_repo = SourceRepository()
        self.evidence_repo = EvidenceRepository()
        self.audit_repo = ResearchAuditRepository()

        # Provider selection
        self.provider: BaseSearchProvider = custom_provider or MockSearchProvider()

        # Primary service facade
        self.service = WebIntelligenceService(
            settings=cfg,
            search_provider=self.provider,
            research_repo=self.research_repo,
            source_repo=self.source_repo,
            evidence_repo=self.evidence_repo,
            audit_repo=self.audit_repo,
        )


_container_instance: WebIntelligenceContainer | None = None


def get_web_intelligence_container(
    custom_provider: BaseSearchProvider | None = None,
) -> WebIntelligenceContainer:
    """Retrieve or initialize the global WebIntelligenceContainer instance."""
    global _container_instance
    if _container_instance is None or custom_provider is not None:
        _container_instance = WebIntelligenceContainer(
            custom_provider=custom_provider
        )
    return _container_instance


def reset_web_intelligence_container() -> None:
    """Reset the global WebIntelligenceContainer instance (used for test isolation)."""
    global _container_instance
    _container_instance = None
