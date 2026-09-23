"""Plan Repository for persisting Plan records."""

from abc import ABC, abstractmethod

from madhav.reasoning.domain.plan import Plan


class PlanRepository(ABC):
    """Abstract interface for Plan persistence."""

    @abstractmethod
    async def save(self, plan: Plan) -> Plan:
        """Save or update plan record."""

    @abstractmethod
    async def get_by_id(self, plan_id: str) -> Plan | None:
        """Find plan by plan_id."""

    @abstractmethod
    async def list_plans(self, owner_id: str, skip: int = 0, limit: int = 50) -> list[Plan]:
        """List plans belonging to owner_id."""

    @abstractmethod
    async def count_plans(self, owner_id: str) -> int:
        """Count plans belonging to owner_id."""

    @abstractmethod
    async def delete(self, plan_id: str) -> bool:
        """Delete plan by plan_id."""


class InMemoryPlanRepository(PlanRepository):
    """In-memory implementation of PlanRepository."""

    def __init__(self) -> None:
        self._store: dict[str, Plan] = {}

    async def save(self, plan: Plan) -> Plan:
        """Save plan in memory."""
        self._store[plan.plan_id] = plan
        return plan

    async def get_by_id(self, plan_id: str) -> Plan | None:
        """Get plan by plan_id."""
        return self._store.get(plan_id)

    async def list_plans(self, owner_id: str, skip: int = 0, limit: int = 50) -> list[Plan]:
        """List plans owned by owner_id."""
        matching = [p for p in self._store.values() if p.owner_id == owner_id]
        matching.sort(key=lambda p: p.updated_at, reverse=True)
        return matching[skip : skip + limit]

    async def count_plans(self, owner_id: str) -> int:
        """Count plans owned by owner_id."""
        return sum(1 for p in self._store.values() if p.owner_id == owner_id)

    async def delete(self, plan_id: str) -> bool:
        """Delete plan by plan_id."""
        if plan_id in self._store:
            del self._store[plan_id]
            return True
        return False
