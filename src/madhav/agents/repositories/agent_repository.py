"""Repository abstractions and in-memory implementation for Agent entities."""

from abc import ABC, abstractmethod

from madhav.agents.domain.agent import Agent
from madhav.agents.domain.enums import AgentRole, AgentStatus, AgentType


class BaseAgentRepository(ABC):
    """Abstract repository interface for Agent definitions."""

    @abstractmethod
    def save(self, agent: Agent) -> Agent:
        """Save or update an agent record."""
        ...

    @abstractmethod
    def get_by_id(self, agent_id: str) -> Agent | None:
        """Retrieve an agent definition by ID."""
        ...

    @abstractmethod
    def delete(self, agent_id: str) -> bool:
        """Delete an agent record."""
        ...

    @abstractmethod
    def list_agents(
        self,
        owner_id: str | None = None,
        status: AgentStatus | None = None,
        type: AgentType | None = None,
        role: AgentRole | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Agent], int]:
        """List agents with filtering and pagination."""
        ...


class MemoryAgentRepository(BaseAgentRepository):
    """In-memory thread-safe implementation of Agent repository."""

    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}

    def save(self, agent: Agent) -> Agent:
        self._agents[agent.id] = agent
        return agent

    def get_by_id(self, agent_id: str) -> Agent | None:
        return self._agents.get(agent_id)

    def delete(self, agent_id: str) -> bool:
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    def list_agents(
        self,
        owner_id: str | None = None,
        status: AgentStatus | None = None,
        type: AgentType | None = None,
        role: AgentRole | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Agent], int]:
        filtered: list[Agent] = []
        for agent in self._agents.values():
            if owner_id and agent.owner_id != owner_id:
                continue
            if status and agent.status != status:
                continue
            if type and agent.type != type:
                continue
            if role and agent.role != role:
                continue
            filtered.append(agent)

        sorted_agents = sorted(filtered, key=lambda a: a.created_at, reverse=True)
        total_count = len(sorted_agents)
        return sorted_agents[offset : offset + limit], total_count


InMemoryAgentRepository = MemoryAgentRepository
AgentRepository = BaseAgentRepository
