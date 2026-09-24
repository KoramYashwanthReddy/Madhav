"""Autonomy Resource Budget Tracking and Circuit Breaker Engine."""

import logging
from typing import Any

from max.autonomy.domain import Mission, MissionStatus
from max.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class MissionCircuitBreaker:
    """Monitors mission failure spikes and consecutive errors to prevent run-away loops."""

    def __init__(self, failure_threshold: int = 5) -> None:
        self.failure_threshold = failure_threshold
        self._consecutive_failures: int = 0
        self._is_tripped: bool = False

    def record_success(self) -> None:
        """Reset consecutive failure counter on step success."""
        self._consecutive_failures = 0

    def record_failure(self) -> bool:
        """Record step failure and trip circuit breaker if threshold is exceeded."""
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.failure_threshold:
            self._is_tripped = True
            logger.critical(
                "Mission circuit breaker TRIPPED! Consecutive failures reached %d.",
                self._consecutive_failures,
            )
        return self._is_tripped

    @property
    def is_tripped(self) -> bool:
        """Return circuit breaker status."""
        return self._is_tripped

    def reset(self) -> None:
        """Reset circuit breaker."""
        self._consecutive_failures = 0
        self._is_tripped = False


class AutonomyBudgetService:
    """Tracks resource consumption against allocated budgets and enforces stop conditions."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def record_usage(
        self,
        mission: Mission,
        execution_seconds: float = 0.0,
        tokens: int = 0,
        tool_calls: int = 0,
        agent_delegations: int = 0,
        files_touched: int = 0,
        retries: int = 0,
        replans: int = 0,
    ) -> tuple[bool, str]:
        """Record resource usage increment and check against mission budget limits."""
        ub = mission.used_budget
        ub["execution_seconds"] += execution_seconds
        ub["tokens"] += tokens
        ub["tool_calls"] += tool_calls
        ub["agent_delegations"] += agent_delegations
        ub["files_touched"] += files_touched
        ub["retries"] += retries
        ub["replans"] += replans

        b = mission.budget

        if ub["execution_seconds"] > b.max_execution_seconds:
            mission.status = MissionStatus.EXPIRED
            return False, f"BUDGET_EXCEEDED: Execution time ({ub['execution_seconds']}s) exceeded max {b.max_execution_seconds}s."

        if ub["tokens"] > b.max_tokens:
            mission.status = MissionStatus.BLOCKED
            return False, f"BUDGET_EXCEEDED: Token usage ({ub['tokens']}) exceeded max budget {b.max_tokens}."

        if ub["tool_calls"] > b.max_tool_calls:
            mission.status = MissionStatus.BLOCKED
            return False, f"BUDGET_EXCEEDED: Tool call count ({ub['tool_calls']}) exceeded max budget {b.max_tool_calls}."

        if ub["agent_delegations"] > b.max_agent_delegations:
            mission.status = MissionStatus.BLOCKED
            return False, f"BUDGET_EXCEEDED: Agent delegation count ({ub['agent_delegations']}) exceeded max {b.max_agent_delegations}."

        if ub["files_touched"] > b.max_files_touched:
            mission.status = MissionStatus.BLOCKED
            return False, f"BUDGET_EXCEEDED: Files touched count ({ub['files_touched']}) exceeded max {b.max_files_touched}."

        if ub["replans"] > b.max_replans:
            mission.status = MissionStatus.FAILED
            return False, f"BUDGET_EXCEEDED: Replanning count ({ub['replans']}) exceeded max limit {b.max_replans}."

        return True, "BUDGET_OK"
