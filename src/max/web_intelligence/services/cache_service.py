"""CacheService for caching search responses and web source content."""

from typing import Any

from max.web_intelligence.repositories.repositories import ResearchCacheRepository


class ResearchCacheService:
    """Manages search query and URL content caching."""

    def __init__(self, cache_repo: ResearchCacheRepository | None = None) -> None:
        self.repo = cache_repo or ResearchCacheRepository()

    def get_cached_search(self, query: str) -> Any | None:
        return self.repo.get_query(query.lower().strip())

    def set_cached_search(self, query: str, data: Any) -> None:
        self.repo.set_query(query.lower().strip(), data)

    def get_cached_url(self, url: str) -> Any | None:
        return self.repo.get_url(url.rstrip("/"))

    def set_cached_url(self, url: str, data: Any) -> None:
        self.repo.set_url(url.rstrip("/"), data)
