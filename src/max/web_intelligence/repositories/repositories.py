"""In-memory repository abstractions for Module 21 — Web Intelligence."""

import logging
from typing import Any

from max.web_intelligence.domain.models import (
    Evidence,
    ResearchAuditEvent,
    ResearchRequest,
    ResearchResult,
    Source,
)

logger = logging.getLogger(__name__)


class ResearchRepository:
    """In-memory repository for research requests and results."""

    def __init__(self) -> None:
        self._requests: dict[str, ResearchRequest] = {}
        self._results: dict[str, ResearchResult] = {}

    def save_request(self, request: ResearchRequest) -> None:
        self._requests[request.id] = request

    def get_request(self, research_id: str) -> ResearchRequest | None:
        return self._requests.get(research_id)

    def save_result(self, result: ResearchResult) -> None:
        self._results[result.research_id] = result

    def get_result(self, research_id: str) -> ResearchResult | None:
        return self._results.get(research_id)

    def list_requests(self, owner_id: str | None = None) -> list[ResearchRequest]:
        reqs = list(self._requests.values())
        if owner_id:
            reqs = [r for r in reqs if r.owner_id == owner_id]
        return reqs


class SourceRepository:
    """In-memory repository for discovered candidate web sources."""

    def __init__(self) -> None:
        self._sources: dict[str, Source] = {}

    def save(self, source: Source) -> None:
        self._sources[source.id] = source

    def get(self, source_id: str) -> Source | None:
        return self._sources.get(source_id)

    def find_by_url(self, research_id: str, url: str) -> Source | None:
        for src in self._sources.values():
            if src.research_id == research_id and src.metadata.url.rstrip("/") == url.rstrip("/"):
                return src
        return None

    def list_by_research(self, research_id: str) -> list[Source]:
        return [s for s in self._sources.values() if s.research_id == research_id]


class EvidenceRepository:
    """In-memory repository for extracted evidence items."""

    def __init__(self) -> None:
        self._evidence: dict[str, Evidence] = {}

    def save(self, evidence: Evidence) -> None:
        self._evidence[evidence.id] = evidence

    def get(self, evidence_id: str) -> Evidence | None:
        return self._evidence.get(evidence_id)

    def list_by_research(self, research_id: str) -> list[Evidence]:
        return [e for e in self._evidence.values() if e.research_id == research_id]


class ResearchAuditRepository:
    """In-memory repository for audit event logging."""

    def __init__(self) -> None:
        self._events: list[ResearchAuditEvent] = []

    def log_event(self, event: ResearchAuditEvent) -> None:
        self._events.append(event)
        logger.info(f"ResearchAudit [{event.research_id}] {event.event_type}: {event.details}")

    def list_by_research(self, research_id: str) -> list[ResearchAuditEvent]:
        return [e for e in self._events if e.research_id == research_id]


class ResearchCacheRepository:
    """In-memory cache for search responses and web document acquisitions."""

    def __init__(self) -> None:
        self._query_cache: dict[str, Any] = {}
        self._url_cache: dict[str, Any] = {}

    def get_query(self, query_key: str) -> Any | None:
        return self._query_cache.get(query_key)

    def set_query(self, query_key: str, data: Any) -> None:
        self._query_cache[query_key] = data

    def get_url(self, url: str) -> Any | None:
        return self._url_cache.get(url)

    def set_url(self, url: str, data: Any) -> None:
        self._url_cache[url] = data

    def clear(self) -> None:
        self._query_cache.clear()
        self._url_cache.clear()
