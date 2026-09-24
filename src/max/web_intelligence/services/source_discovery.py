"""SourceDiscoveryService for discovering, classifying, and deduplicating web sources."""

from urllib.parse import urlparse

from max.web_intelligence.domain.enums import (
    SourceAuthority,
    SourceFreshness,
    SourceType,
)
from max.web_intelligence.domain.models import (
    ResearchQuery,
    ResearchRequest,
    SearchResult,
    Source,
    SourceMetadata,
    SourceTrustMetadata,
)
from max.web_intelligence.providers.base import BaseSearchProvider


class SourceDiscoveryService:
    """Discovers, classifies, and filters candidate web sources."""

    def classify_source_type(self, domain: str, url: str) -> SourceType:
        """Classify source type from domain and URL patterns."""
        d_lower = domain.lower()
        u_lower = url.lower()

        if d_lower.endswith(".gov") or d_lower.endswith(".gov.uk") or "government" in d_lower:
            return SourceType.GOVERNMENT
        elif d_lower.endswith(".edu") or "arxiv.org" in d_lower or "scholar" in d_lower:
            return SourceType.ACADEMIC_PAPER
        elif "docs." in d_lower or "/docs/" in u_lower or "documentation" in d_lower:
            return SourceType.DOCUMENTATION
        elif any(news in d_lower for news in ["news", "bbc", "reuters", "cnn", "nytimes", "techcrunch"]):
            return SourceType.NEWS_ARTICLE
        elif any(forum in d_lower for forum in ["reddit.com", "stackoverflow.com", "discourse"]):
            return SourceType.COMMUNITY_DISCUSSION
        elif "blog" in d_lower or "/blog/" in u_lower:
            return SourceType.BLOG
        elif any(tech in d_lower for tech in ["python.org", "fastapi.", "pydantic."]):
            return SourceType.OFFICIAL_WEBSITE
        elif "org" in d_lower:
            return SourceType.RESEARCH_ORG
        return SourceType.UNKNOWN

    def evaluate_authority(self, source_type: SourceType, domain: str) -> SourceAuthority:
        """Determine source authority tier."""
        if source_type in (SourceType.OFFICIAL_WEBSITE, SourceType.GOVERNMENT, SourceType.DOCUMENTATION, SourceType.ACADEMIC_PAPER):
            return SourceAuthority.PRIMARY_SOURCE
        elif source_type in (SourceType.NEWS_ARTICLE, SourceType.RESEARCH_ORG, SourceType.COMPANY_PUB):
            return SourceAuthority.SECONDARY_SOURCE
        elif source_type in (SourceType.BLOG, SourceType.COMMUNITY_DISCUSSION, SourceType.FORUM):
            return SourceAuthority.TERTIARY_SOURCE
        return SourceAuthority.UNKNOWN

    def evaluate_freshness(self, published_date_str: str | None) -> SourceFreshness:
        """Evaluate freshness tier from publication date string."""
        if not published_date_str:
            return SourceFreshness.UNKNOWN
        if "2026" in published_date_str:
            return SourceFreshness.VERY_FRESH
        elif "2025" in published_date_str:
            return SourceFreshness.FRESH
        elif "2024" in published_date_str:
            return SourceFreshness.RECENT
        return SourceFreshness.STALE

    async def discover_sources(
        self,
        request: ResearchRequest,
        queries: list[ResearchQuery],
        search_provider: BaseSearchProvider,
    ) -> list[Source]:
        """Execute queries and compile deduplicated candidate Source list."""
        from max.web_intelligence.domain.models import SearchRequest

        seen_urls: set[str] = set()
        sources: list[Source] = []

        for q in queries:
            search_req = SearchRequest(
                query=q.normalized_query,
                max_results=request.constraints.max_sources,
                allowed_domains=request.scope.allowed_domains,
                blocked_domains=request.scope.blocked_domains,
            )

            resp = await search_provider.search(search_req)

            for res in resp.results:
                clean_url = res.url.rstrip("/")
                if clean_url in seen_urls:
                    continue
                seen_urls.add(clean_url)

                stype = self.classify_source_type(res.domain, res.url)
                auth = self.evaluate_authority(stype, res.domain)
                fresh = self.evaluate_freshness(res.published_at)

                meta = SourceMetadata(
                    url=res.url,
                    domain=res.domain,
                    title=res.title,
                    published_date=res.published_at,
                    source_type=stype,
                    discovery_query=q.normalized_query,
                )

                trust = SourceTrustMetadata(
                    is_official=(stype == SourceType.OFFICIAL_WEBSITE),
                    is_primary=(auth == SourceAuthority.PRIMARY_SOURCE),
                    has_publication_date=res.published_at is not None,
                )

                src = Source(
                    research_id=request.id,
                    metadata=meta,
                    authority=auth,
                    freshness=fresh,
                    trust=trust,
                )

                sources.append(src)

                if len(sources) >= request.constraints.max_sources:
                    return sources

        return sources
