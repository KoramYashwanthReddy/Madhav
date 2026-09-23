"""Reasoning Repository for persisting ReasoningResult records."""

from abc import ABC, abstractmethod

from max.reasoning.domain.reasoning import ReasoningResult


class ReasoningRepository(ABC):
    """Abstract interface for ReasoningResult persistence."""

    @abstractmethod
    async def save(self, result: ReasoningResult) -> ReasoningResult:
        """Save reasoning result record."""

    @abstractmethod
    async def get_by_request_id(self, request_id: str) -> ReasoningResult | None:
        """Retrieve reasoning result by request_id."""

    @abstractmethod
    async def list_results(
        self, owner_id: str | None = None, skip: int = 0, limit: int = 50
    ) -> list[ReasoningResult]:
        """List reasoning results with optional owner_id filtering."""

    @abstractmethod
    async def delete(self, request_id: str) -> bool:
        """Delete reasoning result record."""


class InMemoryReasoningRepository(ReasoningRepository):
    """In-memory implementation of ReasoningRepository."""

    def __init__(self) -> None:
        self._store: dict[str, ReasoningResult] = {}

    async def save(self, result: ReasoningResult) -> ReasoningResult:
        """Save result in memory."""
        self._store[result.request_id] = result
        return result

    async def get_by_request_id(self, request_id: str) -> ReasoningResult | None:
        """Get result by request_id."""
        return self._store.get(request_id)

    async def list_results(
        self, owner_id: str | None = None, skip: int = 0, limit: int = 50
    ) -> list[ReasoningResult]:
        """List stored reasoning results."""
        matching = list(self._store.values())
        matching.sort(key=lambda r: r.created_at, reverse=True)
        return matching[skip : skip + limit]

    async def delete(self, request_id: str) -> bool:
        """Delete result by request_id."""
        if request_id in self._store:
            del self._store[request_id]
            return True
        return False
