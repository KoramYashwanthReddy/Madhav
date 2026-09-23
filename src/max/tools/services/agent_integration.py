"""Integration service bridging Module 13 Agent Engine ToolRequestIntent to Module 14 ToolInvocationService."""

import logging

from max.agents.domain.agent import ToolRequestIntent
from max.tools.domain.invocation import (
    ToolInvocationRequest,
    ToolInvocationResult,
)
from max.tools.services.invocation_service import ToolInvocationService

logger = logging.getLogger(__name__)


class AgentToolIntegrationService:
    """Service handling ToolRequestIntent objects emitted by Module 13 Agents."""

    def __init__(self, invocation_service: ToolInvocationService | None = None) -> None:
        self.invocation_svc = invocation_service or ToolInvocationService()

    def process_agent_tool_request(self, intent: ToolRequestIntent) -> ToolInvocationResult:
        """Translate Agent Engine ToolRequestIntent into Module 14 ToolInvocationRequest and execute pipeline."""
        logger.info(
            "Processing Agent ToolRequestIntent via Module 14",
            extra={
                "intent_id": intent.intent_id,
                "tool_name": intent.tool_name,
                "agent_id": intent.agent_id,
                "run_id": intent.run_id,
                "task_id": intent.task_id,
            },
        )

        args = getattr(intent, "arguments", None) or getattr(intent, "parameters", {})

        request = ToolInvocationRequest(
            tool_name=intent.tool_name,
            tool_version=getattr(intent, "tool_version", None),
            arguments=args,
            agent_id=intent.agent_id,
            run_id=intent.run_id,
            task_id=intent.task_id,
            metadata={"intent_id": intent.intent_id, "reason": intent.reason},
        )

        return self.invocation_svc.invoke_tool(request)
