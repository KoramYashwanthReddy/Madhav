"""Base provider interface for agent runtime adapters."""

from abc import ABC, abstractmethod
from typing import Any

from max.agents.domain.agent import Agent, PermissionRequestIntent, ToolRequestIntent
from max.agents.domain.enums import NextAction
from max.agents.domain.run import AgentCoordinationRequest, AgentFailure, AgentResult, AgentRun


class BaseAgentAdapter(ABC):
    """Abstract interface for executing agent coordination steps."""

    @abstractmethod
    def execute_coordination_step(
        self,
        request: AgentCoordinationRequest,
        agent: Agent,
        run: AgentRun,
        context_package: Any | None = None,
    ) -> tuple[AgentResult | None, AgentFailure | None, NextAction, list[ToolRequestIntent], list[PermissionRequestIntent]]:
        """Execute a single coordination step producing result, failure, next_action, and intent requests."""
        ...
