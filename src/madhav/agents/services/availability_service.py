"""Agent availability service evaluating status and capacity."""

from pydantic import BaseModel

from madhav.agents.domain.agent import Agent
from madhav.agents.domain.enums import AgentStatus
from madhav.agents.domain.exceptions import AgentNotFoundError
from madhav.agents.repositories.agent_repository import BaseAgentRepository, MemoryAgentRepository
from madhav.agents.repositories.run_repository import (
    BaseAgentRunRepository,
    MemoryAgentRunRepository,
)


class AgentAvailability(BaseModel):
    """Availability evaluation summary for an Agent."""

    agent_id: str
    is_available: bool
    active_runs_count: int
    max_concurrent_tasks: int
    status: AgentStatus


class AgentAvailabilityService:
    """Evaluates whether an agent is available for new run assignments."""

    def __init__(
        self,
        agent_repo: BaseAgentRepository | None = None,
        run_repo: BaseAgentRunRepository | None = None,
    ) -> None:
        self.agent_repo = agent_repo or MemoryAgentRepository()
        self.run_repo = run_repo or MemoryAgentRunRepository()

    def check_availability(self, agent_id: str) -> AgentAvailability:
        """Check availability details for a given agent ID."""
        agent = self.agent_repo.get_by_id(agent_id)
        if not agent:
            raise AgentNotFoundError(f"Agent {agent_id} not found")
        active_runs = self.run_repo.count_active_runs_for_agent(agent_id)
        is_avail = (agent.status == AgentStatus.ACTIVE) and (
            active_runs < agent.limits.max_concurrent_tasks
        )
        return AgentAvailability(
            agent_id=agent.id,
            is_available=is_avail,
            active_runs_count=active_runs,
            max_concurrent_tasks=agent.limits.max_concurrent_tasks,
            status=agent.status,
        )

    @staticmethod
    def is_agent_available(agent: Agent, active_runs_count: int) -> bool:
        """Check if agent is ACTIVE and under its max concurrent task capacity."""
        if agent.status != AgentStatus.ACTIVE:
            return False
        return active_runs_count < agent.limits.max_concurrent_tasks
