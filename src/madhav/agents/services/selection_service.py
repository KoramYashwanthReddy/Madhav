"""Agent selection service for choosing appropriate agents for tasks/runs."""

from pydantic import BaseModel

from madhav.agents.domain.agent import Agent
from madhav.agents.domain.enums import AgentCapability, AgentRole, AgentStatus, AgentType
from madhav.agents.repositories.agent_repository import BaseAgentRepository, MemoryAgentRepository
from madhav.agents.repositories.run_repository import (
    BaseAgentRunRepository,
    MemoryAgentRunRepository,
)
from madhav.agents.services.availability_service import AgentAvailabilityService
from madhav.agents.services.capability_matcher import CapabilityMatcher


class AgentSelectionResult(BaseModel):
    """Structured outcome result of agent selection process."""

    selected_agent_id: str | None = None
    selected_agent_name: str | None = None
    matched: bool = False
    reason: str = ""
    evaluated_agent_count: int = 0


class AgentSelectionService:
    """Selects an optimal available agent deterministically."""

    def __init__(
        self,
        agent_repo: BaseAgentRepository | None = None,
        availability_service: AgentAvailabilityService | None = None,
        run_repo: BaseAgentRunRepository | None = None,
    ) -> None:
        self.agent_repo = agent_repo or MemoryAgentRepository()
        self.run_repo = run_repo or MemoryAgentRunRepository()
        self.availability_service = availability_service or AgentAvailabilityService(
            self.agent_repo, self.run_repo
        )

    def select_agent(
        self,
        required_capabilities: list[AgentCapability] | None = None,
        task_type: str | None = None,
        preferred_role: AgentRole | None = None,
        preferred_type: AgentType | None = None,
        role: AgentRole | None = None,
        type: AgentType | None = None,
        owner_id: str | None = None,
    ) -> AgentSelectionResult:
        """Select an active agent matching criteria, available capacity, sorted deterministically by ID."""
        req_caps = required_capabilities or []
        target_role = preferred_role or role
        target_type = preferred_type or type

        candidates, _ = self.agent_repo.list_agents(owner_id=owner_id, status=AgentStatus.ACTIVE, limit=500)
        matching_agents: list[Agent] = []

        for agent in candidates:
            if target_type and agent.type != target_type:
                continue
            if target_role and agent.role != target_role:
                continue

            # Check capability match
            is_matched, _ = CapabilityMatcher.match_capabilities(req_caps, agent.capabilities)
            if not is_matched:
                continue

            # Check capacity availability
            active_runs = self.run_repo.count_active_runs_for_agent(agent.id)
            if not AgentAvailabilityService.is_agent_available(agent, active_runs):
                continue

            matching_agents.append(agent)

        if not matching_agents:
            return AgentSelectionResult(
                selected_agent_id=None,
                selected_agent_name=None,
                matched=False,
                reason="No active agent available matching requested criteria",
                evaluated_agent_count=len(candidates),
            )

        # Deterministic tie-breaker: Sort by agent.id ascending
        matching_agents.sort(key=lambda a: a.id)
        best = matching_agents[0]

        return AgentSelectionResult(
            selected_agent_id=best.id,
            selected_agent_name=best.name,
            matched=True,
            reason=f"Matched agent '{best.name}' ({best.id})",
            evaluated_agent_count=len(candidates),
        )
