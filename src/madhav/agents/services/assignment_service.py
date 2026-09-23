"""Agent task assignment service."""

from typing import Any

from madhav.agents.domain.assignment import AgentAssignment, AssignmentPriority
from madhav.agents.domain.enums import (
    AgentAssignmentStatus,
    AgentCapability,
    AgentEventType,
    AgentStatus,
)
from madhav.agents.domain.exceptions import (
    AgentAssignmentNotFoundError,
    AgentCapabilityMismatchError,
    AgentInactiveError,
    AgentNotFoundError,
)
from madhav.agents.repositories.agent_repository import BaseAgentRepository, MemoryAgentRepository
from madhav.agents.repositories.assignment_repository import (
    BaseAgentAssignmentRepository,
    MemoryAgentAssignmentRepository,
)
from madhav.agents.services.capability_matcher import CapabilityMatcher
from madhav.agents.services.trace_service import AgentTraceService


class AgentAssignmentService:
    """Service for managing task assignments to agents."""

    def __init__(
        self,
        assignment_repo: BaseAgentAssignmentRepository | None = None,
        agent_repo: BaseAgentRepository | None = None,
        trace_service: AgentTraceService | None = None,
    ) -> None:
        self.assignment_repo = assignment_repo or MemoryAgentAssignmentRepository()
        self.agent_repo = agent_repo or MemoryAgentRepository()
        self.trace_service = trace_service or AgentTraceService()

    def assign_task(
        self,
        agent_id: str,
        task_id: str,
        owner_id: str = "user_default",
        plan_id: str | None = None,
        required_capabilities: list[AgentCapability] | None = None,
        priority: str = "NORMAL",
        reason: str = "Task assigned to agent",
        metadata: dict[str, Any] | None = None,
    ) -> AgentAssignment:
        """Assign a task to an agent."""
        return self.assign_task_to_agent(
            agent_id=agent_id,
            task_id=task_id,
            owner_id=owner_id,
            plan_id=plan_id,
            required_capabilities=required_capabilities,
            priority=priority,
            reason=reason,
            metadata=metadata,
        )

    def assign_task_to_agent(
        self,
        agent_id: str,
        task_id: str,
        owner_id: str = "user_default",
        plan_id: str | None = None,
        required_capabilities: list[AgentCapability] | None = None,
        priority: str = "NORMAL",
        reason: str = "Task assigned to agent",
        metadata: dict[str, Any] | None = None,
    ) -> AgentAssignment:
        """Assign a task to an agent after validating status and capability match."""
        agent = self.agent_repo.get_by_id(agent_id)
        if not agent:
            raise AgentNotFoundError(agent_id)

        if agent.status != AgentStatus.ACTIVE:
            raise AgentInactiveError(agent_id, agent.status.value)

        req_caps = required_capabilities or []
        is_matched, missing = CapabilityMatcher.match_capabilities(req_caps, agent.capabilities)
        if not is_matched:
            raise AgentCapabilityMismatchError(agent_id, [c.value for c in missing])

        # Prevent duplicate active assignment for same agent and task
        existing = self.assignment_repo.get_by_agent_and_task(agent_id, task_id)
        if existing and existing.status in (
            AgentAssignmentStatus.ASSIGNED,
            AgentAssignmentStatus.ACCEPTED,
            AgentAssignmentStatus.STARTED,
        ):
            return existing

        priority_enum = AssignmentPriority(priority) if isinstance(priority, str) else priority

        assignment = AgentAssignment(
            agent_id=agent_id,
            task_id=task_id,
            plan_id=plan_id,
            owner_id=owner_id,
            status=AgentAssignmentStatus.ASSIGNED,
            priority=priority_enum,
            reason=reason,
            metadata=metadata or {},
        )
        saved = self.assignment_repo.save(assignment)

        self.trace_service.record_event(
            event_type=AgentEventType.TASK_ASSIGNED,
            agent_id=agent_id,
            task_id=task_id,
            summary=f"Task '{task_id}' assigned to agent '{agent.name}'",
            metadata={"assignment_id": saved.assignment_id},
        )
        return saved

    def accept_assignment(self, assignment_id: str) -> AgentAssignment:
        return self.update_assignment_status(assignment_id, AgentAssignmentStatus.ACCEPTED)

    def start_assignment(self, assignment_id: str) -> AgentAssignment:
        return self.update_assignment_status(assignment_id, AgentAssignmentStatus.STARTED)

    def complete_assignment(self, assignment_id: str) -> AgentAssignment:
        return self.update_assignment_status(assignment_id, AgentAssignmentStatus.COMPLETED)

    def fail_assignment(self, assignment_id: str) -> AgentAssignment:
        return self.update_assignment_status(assignment_id, AgentAssignmentStatus.FAILED)

    def cancel_assignment(self, assignment_id: str) -> AgentAssignment:
        return self.update_assignment_status(assignment_id, AgentAssignmentStatus.CANCELLED)

    def list_assignments_for_agent(self, agent_id: str) -> list[AgentAssignment]:
        asgns, _ = self.assignment_repo.list_assignments(agent_id=agent_id, limit=500)
        return asgns

    def update_assignment_status(
        self, assignment_id: str, status: AgentAssignmentStatus
    ) -> AgentAssignment:
        """Update assignment lifecycle status."""
        asgn = self.assignment_repo.get_by_id(assignment_id)
        if not asgn:
            raise AgentAssignmentNotFoundError(f"Assignment '{assignment_id}' not found.")

        updated_dict = asgn.model_dump()
        updated_dict["status"] = status
        new_asgn = AgentAssignment(**updated_dict)
        saved = self.assignment_repo.save(new_asgn)

        event_type = (
            AgentEventType.TASK_ACCEPTED
            if status == AgentAssignmentStatus.ACCEPTED
            else AgentEventType.TASK_REJECTED
            if status == AgentAssignmentStatus.REJECTED
            else AgentEventType.TASK_ASSIGNED
        )
        self.trace_service.record_event(
            event_type=event_type,
            agent_id=asgn.agent_id,
            task_id=asgn.task_id,
            summary=f"Assignment status updated to '{status.value}'",
            metadata={"assignment_id": assignment_id},
        )
        return saved
