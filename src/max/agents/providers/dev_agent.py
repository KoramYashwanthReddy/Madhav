"""Deterministic development agent adapter for 100% offline testing."""

from typing import Any

from max.agents.domain.agent import Agent, PermissionRequestIntent, ToolRequestIntent
from max.agents.domain.enums import AgentRunStatus, FailureCategory, NextAction
from max.agents.domain.run import AgentCoordinationRequest, AgentFailure, AgentResult, AgentRun
from max.agents.providers.base import BaseAgentAdapter


class DevelopmentAgent(BaseAgentAdapter):
    """Deterministic development agent implementation requiring zero external model credentials."""

    def execute_coordination_step(
        self,
        request: AgentCoordinationRequest,
        agent: Agent,
        run: AgentRun,
        context_package: Any | None = None,
    ) -> tuple[AgentResult | None, AgentFailure | None, NextAction, list[ToolRequestIntent], list[PermissionRequestIntent]]:
        """Produce deterministic coordination outcomes based on request parameters."""
        obj_lower = request.objective.lower() if request.objective else ""
        sim_action = request.metadata.get("simulate_next_action", "")

        # Handle failure test case
        if sim_action == "FAIL" or "fail" in obj_lower:
            failure = AgentFailure(
                error_code="DEV_INTENTIONAL_FAILURE",
                message=f"Development agent triggered simulated failure for objective: '{request.objective}'",
                category=FailureCategory.TASK_ERROR,
                retryable=True,
                task_id=request.task_id,
                step_id=request.plan_step_id,
            )
            return None, failure, NextAction.FAIL, [], []

        # Handle tool request intent test case
        if sim_action == "REQUEST_TOOL" or "tool" in obj_lower:
            tool_intent = ToolRequestIntent(
                run_id=run.run_id,
                agent_id=agent.id,
                task_id=request.task_id,
                requested_capability="SEARCH",
                tool_name="web_search",
                parameters={"query": request.objective},
                reason="Requested search tool capability",
                status="NOT_IMPLEMENTED",
            )
            return None, None, NextAction.REQUEST_TOOL, [tool_intent], []

        # Handle permission request intent test case
        if sim_action == "REQUEST_PERMISSION" or "permission" in obj_lower:
            perm_intent = PermissionRequestIntent(
                run_id=run.run_id,
                agent_id=agent.id,
                task_id=request.task_id,
                requested_permission="EXECUTE_COMMAND",
                resource="terminal",
                reason="Requested permission boundary check",
                status="NOT_IMPLEMENTED",
            )
            return None, None, NextAction.REQUEST_PERMISSION, [], [perm_intent]

        # Handle delegation request test case
        if sim_action == "DELEGATE" or "delegate" in obj_lower:
            return None, None, NextAction.DELEGATE, [], []

        # Standard successful coordination result
        result = AgentResult(
            status=AgentRunStatus.COMPLETED,
            summary=f"Development agent successfully coordinated objective: '{request.objective}'",
            completed_tasks=[request.task_id] if request.task_id else [],
            observations=[
                f"Agent '{agent.name}' (role: {agent.role.value}) completed coordination.",
                f"Execution mode: {request.execution_mode.value}",
            ],
            metadata={
                "provider": "DevelopmentAgent",
                "plan_id": request.plan_id,
                "plan_step_id": request.plan_step_id,
            },
        )
        return result, None, NextAction.COMPLETE, [], []
