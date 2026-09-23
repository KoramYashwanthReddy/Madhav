"""Central AgentCoordinator orchestrating task coordination, AI runtime invocation, and boundary checks."""

import logging

from max.agents.domain.agent import Agent, PermissionRequestIntent, ToolRequestIntent
from max.agents.domain.assignment import AgentAssignment
from max.agents.domain.enums import (
    AgentAssignmentStatus,
    AgentRunStatus,
    NextAction,
)
from max.agents.domain.exceptions import AgentUnavailableError
from max.agents.domain.run import (
    AgentCoordinationRequest,
    AgentCoordinationResponse,
)
from max.agents.providers.base import BaseAgentAdapter
from max.agents.providers.dev_agent import DevelopmentAgent
from max.agents.services.agent_service import AgentService
from max.agents.services.assignment_service import AgentAssignmentService
from max.agents.services.boundaries import PermissionCheckPort, ToolExecutionGateway
from max.agents.services.delegation_service import AgentDelegationService
from max.agents.services.run_service import AgentRunService
from max.agents.services.selection_service import AgentSelectionService
from max.agents.services.trace_service import AgentTraceService
from max.context.services.manager import ContextManager
from max.tasks.services.task_service import TaskService

logger = logging.getLogger(__name__)


class AgentCoordinator:
    """Orchestration coordinator directing agent execution runs, context assembly, and boundary intents."""

    def __init__(
        self,
        agent_service: AgentService | None = None,
        run_service: AgentRunService | None = None,
        assignment_service: AgentAssignmentService | None = None,
        selection_service: AgentSelectionService | None = None,
        trace_service: AgentTraceService | None = None,
        delegation_service: AgentDelegationService | None = None,
        task_service: TaskService | None = None,
        context_manager: ContextManager | None = None,
        agent_adapter: BaseAgentAdapter | None = None,
        dev_agent: BaseAgentAdapter | None = None,
        tool_gateway: ToolExecutionGateway | None = None,
        permission_gateway: PermissionCheckPort | None = None,
    ) -> None:
        self.agent_service = agent_service or AgentService()
        self.run_service = run_service or AgentRunService(agent_repo=self.agent_service.agent_repo)
        self.assignment_service = assignment_service or AgentAssignmentService(
            agent_repo=self.agent_service.agent_repo
        )
        self.selection_service = selection_service or AgentSelectionService(
            agent_repo=self.agent_service.agent_repo, run_repo=self.run_service.run_repo
        )
        self.trace_service = trace_service or AgentTraceService()
        self.delegation_service = delegation_service or AgentDelegationService(
            agent_repo=self.agent_service.agent_repo
        )
        self.task_service = task_service or TaskService()
        self.context_manager = context_manager or ContextManager()
        self.adapter = dev_agent or agent_adapter or DevelopmentAgent()
        self.tool_gateway = tool_gateway or ToolExecutionGateway()
        self.permission_gateway = permission_gateway or PermissionCheckPort()

    def coordinate(self, request: AgentCoordinationRequest) -> AgentCoordinationResponse:
        """Alias method for coordinate_task."""
        return self.coordinate_task(request)

    def coordinate_task(self, request: AgentCoordinationRequest) -> AgentCoordinationResponse:
        """Execute agent task coordination workflow."""
        # 1. Select or fetch Agent
        agent: Agent
        if request.agent_id:
            agent = self.agent_service.get_agent(request.agent_id)
        else:
            selection_res = self.selection_service.select_agent(owner_id=request.owner_id)
            if not selection_res.matched or not selection_res.selected_agent_id:
                raise AgentUnavailableError(
                    selection_res.reason or "No available agent matched criteria"
                )
            agent = self.agent_service.get_agent(selection_res.selected_agent_id)

        # 2. Validate Task reference if task_id provided
        if request.task_id:
            task_id = request.task_id
            try:
                task = self.task_service.get_task(request.task_id)
                task_id = task.id
            except Exception:
                task_id = request.task_id

            # Create/start assignment
            asgn = self.assignment_service.assign_task_to_agent(
                agent_id=agent.id,
                task_id=task_id,
                owner_id=request.owner_id,
                plan_id=request.plan_id,
            )
            self.assignment_service.update_assignment_status(
                asgn.assignment_id, AgentAssignmentStatus.STARTED
            )

        # 3. Context Package preparation (stub/fallback safe)
        context_package = None

        # 4. Create & Initialize AgentRun
        run = self.run_service.create_run(
            agent_id=agent.id,
            owner_id=request.owner_id,
            task_id=request.task_id,
            plan_id=request.plan_id,
            plan_step_id=request.plan_step_id,
            conversation_id=request.conversation_id,
            execution_mode=request.execution_mode,
            metadata=request.metadata,
        )

        self.run_service.transition_run_status(
            run.run_id, AgentRunStatus.INITIALIZING, reason="Initializing run context"
        )
        self.run_service.transition_run_status(
            run.run_id, AgentRunStatus.READY, reason="Ready for execution"
        )
        self.run_service.transition_run_status(
            run.run_id, AgentRunStatus.RUNNING, reason="Executing coordination step"
        )

        # 5. Invoke Agent Adapter (DevelopmentAgent)
        result, failure, next_action, tool_requests, perm_requests = (
            self.adapter.execute_coordination_step(
                request=request,
                agent=agent,
                run=run,
                context_package=context_package,
            )
        )

        # 6. Process Tool & Permission Boundary Intents (NO ACTION EXECUTION / NO PERMISSION GRANTED)
        processed_tools: list[ToolRequestIntent] = []
        for tool_req in tool_requests:
            processed_tools.append(self.tool_gateway.process_tool_request(tool_req))

        processed_perms: list[PermissionRequestIntent] = []
        for perm_req in perm_requests:
            processed_perms.append(self.permission_gateway.check_permission(perm_req))

        # 7. Update AgentRun Final Status based on next_action
        final_status = AgentRunStatus.RUNNING
        if next_action in (NextAction.COMPLETE, NextAction.FAIL):
            final_status = AgentRunStatus.COMPLETED if result else AgentRunStatus.FAILED
        elif next_action in (
            NextAction.REQUEST_TOOL,
            NextAction.REQUEST_PERMISSION,
            NextAction.WAIT,
        ):
            final_status = AgentRunStatus.WAITING

        updated_run = self.run_service.transition_run_status(
            run_id=run.run_id,
            target_status=final_status,
            reason=f"Coordination step produced NextAction '{next_action.value}'",
            result=result,
            failure=failure,
            next_action=next_action,
            tool_requests=processed_tools,
            permission_requests=processed_perms,
        )

        # 8. Update Assignment status if linked
        if request.task_id:
            asgn_record: AgentAssignment | None = (
                self.assignment_service.assignment_repo.get_by_agent_and_task(
                    agent.id, request.task_id
                )
            )
            if asgn_record:
                asgn_status = (
                    AgentAssignmentStatus.COMPLETED
                    if final_status == AgentRunStatus.COMPLETED
                    else AgentAssignmentStatus.FAILED
                    if final_status == AgentRunStatus.FAILED
                    else AgentAssignmentStatus.STARTED
                )
                self.assignment_service.update_assignment_status(
                    asgn_record.assignment_id, asgn_status
                )

        trace = self.trace_service.get_trace_for_run(run.run_id)

        logger.info(
            "Agent task coordination completed",
            extra={
                "run_id": run.run_id,
                "agent_id": agent.id,
                "next_action": next_action.value,
                "status": final_status.value,
            },
        )

        return AgentCoordinationResponse(
            run_id=updated_run.run_id,
            agent_id=agent.id,
            task_id=request.task_id,
            status=updated_run.status,
            result=updated_run.result,
            failure=updated_run.failure,
            next_action=updated_run.next_action,
            tool_requests=processed_tools,
            permission_requests=processed_perms,
            trace_reference=run.run_id,
            metadata={"events_count": len(trace.events)},
        )
