"""Abstract base search provider interface for Module 21."""

from abc import ABC, abstractmethod
from typing import Any

from max.web_intelligence.domain.models import SearchRequest, SearchResponse


class BaseSearchProvider(ABC):
    """Provider-neutral search engine interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return canonical provider identifier name."""
        pass

    @abstractmethod
    async def search(self, request: SearchRequest) -> SearchResponse:
        """Execute a search request and return structured search results."""
        pass

    @abstractmethod
    async def health(self) -> dict[str, Any]:
        """Return provider health status details."""
        pass

    @abstractmethod
    def capabilities(self) -> list[str]:
        """Return list of supported search capabilities."""
        pass
