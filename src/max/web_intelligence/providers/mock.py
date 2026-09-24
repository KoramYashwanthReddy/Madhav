"""Deterministic in-memory MockSearchProvider for testing Module 21."""

from typing import Any

from max.web_intelligence.domain.models import (
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from max.web_intelligence.providers.base import BaseSearchProvider


class MockSearchProvider(BaseSearchProvider):
    """Safe, deterministic in-memory search provider for unit testing and offline development."""

    def __init__(self, custom_knowledge: list[dict[str, Any]] | None = None) -> None:
        self._custom_knowledge = custom_knowledge or []
        self._default_results: list[dict[str, Any]] = [
            {
                "query_keyword": "python",
                "title": "Python Programming Language Official",
                "url": "https://www.python.org",
                "domain": "www.python.org",
                "snippet": "Official website for Python programming language. Version 3.12 release notes and documentation.",
                "published_at": "2026-01-15",
            },
            {
                "query_keyword": "fastapi",
                "title": "FastAPI Web Framework Documentation",
                "url": "https://fastapi.tiangolo.com",
                "domain": "fastapi.tiangolo.com",
                "snippet": "FastAPI is a modern, fast web framework for building APIs with Python 3.8+ based on standard Python type hints.",
                "published_at": "2026-02-10",
            },
            {
                "query_keyword": "pydantic",
                "title": "Pydantic V2 Release & Architecture Guide",
                "url": "https://docs.pydantic.dev",
                "domain": "docs.pydantic.dev",
                "snippet": "Data validation using Python type hints. Rust-powered core validation logic.",
                "published_at": "2025-11-20",
            },
            {
                "query_keyword": "ai",
                "title": "Artificial Intelligence Research Progress 2026",
                "url": "https://ai.research-org.org/progress",
                "domain": "ai.research-org.org",
                "snippet": "Comprehensive analysis of agentic AI systems, context management, and reasoning models in 2026.",
                "published_at": "2026-03-01",
            },
            {
                "query_keyword": "technology",
                "title": "Tech Industry Annual Benchmark Report",
                "url": "https://tech-news.example.com/report-2026",
                "domain": "tech-news.example.com",
                "snippet": "Key trends in AI agents, automated development, browser automation, and security sandboxes.",
                "published_at": "2026-02-28",
            },
        ]

    @property
    def name(self) -> str:
        return "mock"

    def capabilities(self) -> list[str]:
        return ["keyword_search", "domain_filter", "deterministic_mock"]

    async def health(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "provider": self.name,
            "custom_item_count": len(self._custom_knowledge),
        }

    def add_mock_result(self, title: str, url: str, snippet: str, published_at: str | None = None) -> None:
        """Helper method to dynamically inject custom search result items for testing."""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc or "example.com"
        self._custom_knowledge.append({
            "query_keyword": "*",
            "title": title,
            "url": url,
            "domain": domain,
            "snippet": snippet,
            "published_at": published_at,
        })

    async def search(self, request: SearchRequest) -> SearchResponse:
        """Search mock corpus matching query terms and domain constraints."""
        q_lower = request.query.lower()
        matched: list[SearchResult] = []

        all_pool = self._custom_knowledge + self._default_results

        rank_counter = 1
        for item in all_pool:
            kw = item.get("query_keyword", "*")
            url = item["url"]
            domain = item.get("domain", "")

            # Domain filtering checks
            if request.allowed_domains and not any(d in domain for d in request.allowed_domains):
                continue
            if request.blocked_domains and any(d in domain for d in request.blocked_domains):
                continue

            # Keyword match or wildcard
            if kw == "*" or kw.lower() in q_lower or any(word in q_lower for word in item["title"].lower().split()):
                res = SearchResult(
                    query_id=f"qry_{hash(request.query) & 0xffffffff:08x}",
                    title=item["title"],
                    url=url,
                    domain=domain,
                    snippet=item["snippet"],
                    published_at=item.get("published_at"),
                    provider_name=self.name,
                    rank=rank_counter,
                )
                matched.append(res)
                rank_counter += 1
                if len(matched) >= request.max_results:
                    break

        # Fallback default item if nothing matched
        if not matched:
            matched.append(
                SearchResult(
                    query_id=f"qry_{hash(request.query) & 0xffffffff:08x}",
                    title=f"Search Results for '{request.query}'",
                    url=f"https://search.example.com/q={request.query.replace(' ', '+')}",
                    domain="search.example.com",
                    snippet=f"Overview of information and search findings for query '{request.query}'.",
                    published_at="2026-01-01",
                    provider_name=self.name,
                    rank=1,
                )
            )

        return SearchResponse(
            query=request.query,
            provider_name=self.name,
            results=matched,
            total_count=len(matched),
        )
