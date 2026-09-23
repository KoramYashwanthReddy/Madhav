"""Agent definition lifecycle service."""

import logging
from datetime import datetime
from typing import Any

from madhav.agents.domain.agent import Agent, AgentConfiguration, AgentLimits
from madhav.agents.domain.enums import (
    AgentCapability,
    AgentEventType,
    AgentRole,
    AgentStatus,
    AgentType,
)
from madhav.agents.domain.exceptions import AgentNotFoundError
from madhav.agents.repositories.agent_repository import BaseAgentRepository, MemoryAgentRepository
from madhav.agents.services.state_machine import AgentStateMachine
from madhav.agents.services.trace_service import AgentTraceService
from madhav.config.sections import AgentSettings

logger = logging.getLogger(__name__)


class AgentService:
    """Service managing Agent definitions and lifecycle state transitions."""

    def __init__(
        self,
        agent_repository: BaseAgentRepository | None = None,
        trace_service: AgentTraceService | None = None,
        settings: AgentSettings | None = None,
    ) -> None:
        self.agent_repo = agent_repository or MemoryAgentRepository()
        self.trace_service = trace_service or AgentTraceService()
        self.settings = settings or AgentSettings()

    @property
    def repository(self) -> BaseAgentRepository:
        return self.agent_repo

    def create_agent(
        self,
        owner_id: str,
        name: str,
        description: str = "",
        type: AgentType = AgentType.GENERAL,
        role: AgentRole = AgentRole.ASSISTANT,
        capabilities: list[AgentCapability] | None = None,
        configuration: AgentConfiguration | None = None,
        limits: AgentLimits | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Agent:
        """Create a new Agent definition."""
        agent = Agent(
            owner_id=owner_id,
            name=name,
            description=description,
            type=type,
            role=role,
            status=AgentStatus.CREATED,
            capabilities=capabilities or [AgentCapability.TASK_COORDINATION],
            configuration=configuration or AgentConfiguration(),
            limits=limits or AgentLimits(),
            metadata=metadata or {},
        )
        saved = self.agent_repo.save(agent)

        self.trace_service.record_event(
            event_type=AgentEventType.AGENT_CREATED,
            agent_id=saved.id,
            summary=f"Agent definition '{saved.name}' created with role '{saved.role.value}'",
            metadata={"owner_id": owner_id},
        )

        logger.info("Agent created", extra={"agent_id": saved.id, "agent_name": saved.name, "owner_id": owner_id})
        return saved

    def get_agent(self, agent_id: str) -> Agent:
        """Retrieve an agent by ID."""
        agent = self.agent_repo.get_by_id(agent_id)
        if not agent:
            raise AgentNotFoundError(agent_id)
        return agent

    def update_agent(
        self,
        agent_id: str,
        name: str | None = None,
        description: str | None = None,
        type: AgentType | None = None,
        role: AgentRole | None = None,
        capabilities: list[AgentCapability] | None = None,
        configuration: AgentConfiguration | None = None,
        limits: AgentLimits | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Agent:
        """Update agent properties."""
        agent = self.get_agent(agent_id)
        updated_dict = agent.model_dump()

        if name is not None:
            updated_dict["name"] = name
        if description is not None:
            updated_dict["description"] = description
        if type is not None:
            updated_dict["type"] = type
        if role is not None:
            updated_dict["role"] = role
        if capabilities is not None:
            updated_dict["capabilities"] = capabilities
        if configuration is not None:
            updated_dict["configuration"] = configuration
        if limits is not None:
            updated_dict["limits"] = limits
        if metadata is not None:
            merged_meta = dict(agent.metadata)
            merged_meta.update(metadata)
            updated_dict["metadata"] = merged_meta

        updated_dict["updated_at"] = datetime.utcnow()
        new_agent = Agent(**updated_dict)
        return self.agent_repo.save(new_agent)

    def transition_agent_status(
        self, agent_id: str, target_status: AgentStatus, reason: str = "Status update"
    ) -> Agent:
        """Transition agent lifecycle status."""
        agent = self.get_agent(agent_id)
        AgentStateMachine.validate_transition(agent.status, target_status, reason=reason)

        updated_dict = agent.model_dump()
        updated_dict["status"] = target_status
        updated_dict["updated_at"] = datetime.utcnow()

        saved = self.agent_repo.save(Agent(**updated_dict))

        event_map = {
            AgentStatus.ACTIVE: AgentEventType.AGENT_ACTIVATED,
            AgentStatus.PAUSED: AgentEventType.AGENT_PAUSED,
            AgentStatus.DISABLED: AgentEventType.AGENT_DISABLED,
        }
        event_type = event_map.get(target_status, AgentEventType.AGENT_ACTIVATED)

        self.trace_service.record_event(
            event_type=event_type,
            agent_id=saved.id,
            summary=f"Agent '{saved.name}' status updated to '{target_status.value}'",
        )
        return saved

    def activate_agent(self, agent_id: str) -> Agent:
        """Move agent status to ACTIVE."""
        return self.transition_agent_status(agent_id, AgentStatus.ACTIVE, reason="Agent activated")

    def pause_agent(self, agent_id: str) -> Agent:
        """Move agent status to PAUSED."""
        return self.transition_agent_status(agent_id, AgentStatus.PAUSED, reason="Agent paused")

    def disable_agent(self, agent_id: str) -> Agent:
        """Move agent status to DISABLED."""
        return self.transition_agent_status(agent_id, AgentStatus.DISABLED, reason="Agent disabled")

    def archive_agent(self, agent_id: str) -> Agent:
        """Move agent status to ARCHIVED."""
        return self.transition_agent_status(agent_id, AgentStatus.ARCHIVED, reason="Agent archived")

    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent record."""
        self.get_agent(agent_id)
        return self.agent_repo.delete(agent_id)

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
        effective_limit = min(limit, self.settings.max_page_size)
        return self.agent_repo.list_agents(
            owner_id=owner_id,
            status=status,
            type=type,
            role=role,
            limit=effective_limit,
            offset=offset,
        )
