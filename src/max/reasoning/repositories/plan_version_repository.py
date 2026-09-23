"""Plan Version Repository for historical plan version snapshots."""

from abc import ABC, abstractmethod

from max.reasoning.domain.plan import PlanVersion


class PlanVersionRepository(ABC):
    """Abstract interface for PlanVersion snapshot persistence."""

    @abstractmethod
    async def save_version(self, version: PlanVersion) -> PlanVersion:
        """Save a new version snapshot."""

    @abstractmethod
    async def get_version(self, plan_id: str, version_number: int) -> PlanVersion | None:
        """Get specific version snapshot for a plan."""

    @abstractmethod
    async def get_by_version_id(self, version_id: str) -> PlanVersion | None:
        """Get version snapshot by version_id."""

    @abstractmethod
    async def list_versions(self, plan_id: str) -> list[PlanVersion]:
        """List all version snapshots for a plan ordered by version number."""


class InMemoryPlanVersionRepository(PlanVersionRepository):
    """In-memory implementation of PlanVersionRepository."""

    def __init__(self) -> None:
        # store: plan_id -> list[PlanVersion]
        self._store: dict[str, list[PlanVersion]] = {}

    async def save_version(self, version: PlanVersion) -> PlanVersion:
        """Save version snapshot."""
        if version.plan_id not in self._store:
            self._store[version.plan_id] = []
        self._store[version.plan_id].append(version)
        return version

    async def get_version(self, plan_id: str, version_number: int) -> PlanVersion | None:
        """Get version by version_number."""
        versions = self._store.get(plan_id, [])
        for v in versions:
            if v.version_number == version_number:
                return v
        return None

    async def get_by_version_id(self, version_id: str) -> PlanVersion | None:
        """Get version snapshot by version_id."""
        for versions in self._store.values():
            for v in versions:
                if v.version_id == version_id:
                    return v
        return None

    async def list_versions(self, plan_id: str) -> list[PlanVersion]:
        """List version snapshots for plan_id."""
        versions = list(self._store.get(plan_id, []))
        versions.sort(key=lambda v: v.version_number)
        return versions
