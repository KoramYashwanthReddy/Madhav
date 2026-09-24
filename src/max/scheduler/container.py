"""Dependency Injection container for Module 28 — Scheduler & Automation Engine."""

from __future__ import annotations

import logging

from max.config.settings import get_settings
from max.scheduler.integrations.adapters import (
    AgentEngineAdapter,
    NotificationAdapter,
    PermissionSecurityAdapter,
    TaskEngineAdapter,
    ToolRegistryAdapter,
)
from max.scheduler.repositories.repositories import (
    MemoryAuditRepository,
    MemoryAutomationRepository,
    MemoryExecutionRepository,
    MemoryScheduleRepository,
    MemorySchedulerLockRepository,
    MemoryTriggerRepository,
)
from max.scheduler.services.automation_engine import AutomationEngineService
from max.scheduler.services.deterministic_backend import DeterministicSchedulerBackend
from max.scheduler.services.scheduler_service import SchedulerService

logger = logging.getLogger(__name__)


class SchedulerContainer:
    """Dependency Injection container managing components of Module 28."""

    def __init__(self) -> None:
        self.settings = get_settings().scheduler

        # Repositories
        self.schedule_repo = MemoryScheduleRepository()
        self.automation_repo = MemoryAutomationRepository()
        self.execution_repo = MemoryExecutionRepository()
        self.trigger_repo = MemoryTriggerRepository()
        self.lock_repo = MemorySchedulerLockRepository()
        self.audit_repo = MemoryAuditRepository()

        # Integration Adapters
        self.task_adapter = TaskEngineAdapter()
        self.agent_adapter = AgentEngineAdapter()
        self.tool_adapter = ToolRegistryAdapter()
        self.security_adapter = PermissionSecurityAdapter()
        self.notification_adapter = NotificationAdapter()

        # Automation Engine Service
        self.automation_engine = AutomationEngineService(
            automation_repo=self.automation_repo,
            execution_repo=self.execution_repo,
            audit_repo=self.audit_repo,
            task_adapter=self.task_adapter,
            agent_adapter=self.agent_adapter,
            tool_adapter=self.tool_adapter,
            security_adapter=self.security_adapter,
            notification_adapter=self.notification_adapter,
            circuit_breaker_threshold=self.settings.circuit_breaker_threshold,
            max_executions_per_minute=self.settings.max_executions_per_minute,
        )

        # Scheduler Service
        self.scheduler_service = SchedulerService(
            schedule_repo=self.schedule_repo,
            execution_repo=self.execution_repo,
            trigger_repo=self.trigger_repo,
            lock_repo=self.lock_repo,
            audit_repo=self.audit_repo,
            automation_engine=self.automation_engine,
            lock_timeout_seconds=self.settings.lock_timeout_seconds,
        )

        # Deterministic Test Backend
        self.deterministic_backend = DeterministicSchedulerBackend(self.scheduler_service)


_SCHEDULER_CONTAINER_INSTANCE: SchedulerContainer | None = None


def get_scheduler_container() -> SchedulerContainer:
    """Get global SchedulerContainer singleton instance."""
    global _SCHEDULER_CONTAINER_INSTANCE
    if _SCHEDULER_CONTAINER_INSTANCE is None:
        _SCHEDULER_CONTAINER_INSTANCE = SchedulerContainer()
    return _SCHEDULER_CONTAINER_INSTANCE


def reset_scheduler_container() -> None:
    """Reset global SchedulerContainer instance for test isolation."""
    global _SCHEDULER_CONTAINER_INSTANCE
    _SCHEDULER_CONTAINER_INSTANCE = None
