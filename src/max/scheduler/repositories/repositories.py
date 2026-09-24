"""Repository abstractions and thread-safe in-memory implementations for Module 28."""

from __future__ import annotations

import builtins
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from threading import Lock

from max.scheduler.domain.models import (
    Automation,
    Execution,
    Schedule,
    SchedulerAuditEvent,
    SchedulerLock,
    Trigger,
)


class BaseScheduleRepository(ABC):
    """Abstract repository interface for Schedules."""

    @abstractmethod
    def save(self, schedule: Schedule) -> None:
        pass

    @abstractmethod
    def get_by_id(self, schedule_id: str) -> Schedule | None:
        pass

    @abstractmethod
    def list(
        self,
        owner_id: str | None = None,
        status: str | None = None,
        schedule_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> builtins.list[Schedule]:
        pass

    @abstractmethod
    def get_due_schedules(self, cutoff_time: datetime) -> builtins.list[Schedule]:
        pass

    @abstractmethod
    def delete(self, schedule_id: str) -> bool:
        pass


class BaseAutomationRepository(ABC):
    """Abstract repository interface for Automations."""

    @abstractmethod
    def save(self, automation: Automation) -> None:
        pass

    @abstractmethod
    def get_by_id(self, automation_id: str) -> Automation | None:
        pass

    @abstractmethod
    def list(
        self,
        owner_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Automation]:
        pass

    @abstractmethod
    def delete(self, automation_id: str) -> bool:
        pass


class BaseExecutionRepository(ABC):
    """Abstract repository interface for Executions."""

    @abstractmethod
    def save(self, execution: Execution) -> None:
        pass

    @abstractmethod
    def get_by_id(self, execution_id: str) -> Execution | None:
        pass

    @abstractmethod
    def get_by_idempotency_key(self, key: str) -> Execution | None:
        pass

    @abstractmethod
    def list(
        self,
        automation_id: str | None = None,
        schedule_id: str | None = None,
        owner_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Execution]:
        pass

    @abstractmethod
    def count_active_executions(
        self, automation_id: str | None = None, owner_id: str | None = None
    ) -> int:
        pass


class BaseTriggerRepository(ABC):
    """Abstract repository interface for Triggers."""

    @abstractmethod
    def save(self, trigger: Trigger) -> None:
        pass

    @abstractmethod
    def get_by_id(self, trigger_id: str) -> Trigger | None:
        pass

    @abstractmethod
    def list(self, trigger_type: str | None = None, status: str | None = None) -> list[Trigger]:
        pass


class BaseSchedulerLockRepository(ABC):
    """Abstract repository interface for Scheduler Locks."""

    @abstractmethod
    def acquire(self, resource_id: str, owner_id: str, timeout_seconds: float) -> bool:
        pass

    @abstractmethod
    def release(self, resource_id: str, owner_id: str) -> bool:
        pass

    @abstractmethod
    def is_locked(self, resource_id: str) -> bool:
        pass


class BaseAuditRepository(ABC):
    """Abstract repository interface for Audit Events."""

    @abstractmethod
    def save(self, audit_event: SchedulerAuditEvent) -> None:
        pass

    @abstractmethod
    def list(
        self,
        schedule_id: str | None = None,
        automation_id: str | None = None,
        execution_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SchedulerAuditEvent]:
        pass


# In-Memory Implementations

class MemoryScheduleRepository(BaseScheduleRepository):
    """Thread-safe in-memory schedule storage."""

    def __init__(self) -> None:
        self._schedules: dict[str, Schedule] = {}
        self._lock = Lock()

    def save(self, schedule: Schedule) -> None:
        with self._lock:
            self._schedules[schedule.schedule_id] = schedule.model_copy(deep=True)

    def get_by_id(self, schedule_id: str) -> Schedule | None:
        with self._lock:
            item = self._schedules.get(schedule_id)
            return item.model_copy(deep=True) if item else None

    def list(
        self,
        owner_id: str | None = None,
        status: str | None = None,
        schedule_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Schedule]:
        with self._lock:
            results = list(self._schedules.values())

        if owner_id:
            results = [s for s in results if s.owner_id == owner_id]
        if status:
            results = [s for s in results if s.status.value == status or s.status == status]
        if schedule_type:
            results = [
                s for s in results if s.schedule_type.value == schedule_type or s.schedule_type == schedule_type
            ]

        return [s.model_copy(deep=True) for s in results[offset : offset + limit]]

    def get_due_schedules(self, cutoff_time: datetime) -> builtins.list[Schedule]:
        if cutoff_time.tzinfo is None:
            cutoff_time = cutoff_time.replace(tzinfo=UTC)

        with self._lock:
            due: list[Schedule] = []
            for s in self._schedules.values():
                if s.status.value in ("SCHEDULED", "READY") and s.next_run_at:
                    next_run = s.next_run_at
                    if next_run.tzinfo is None:
                        next_run = next_run.replace(tzinfo=UTC)
                    if next_run <= cutoff_time:
                        due.append(s.model_copy(deep=True))
            return due

    def delete(self, schedule_id: str) -> bool:
        with self._lock:
            return self._schedules.pop(schedule_id, None) is not None


class MemoryAutomationRepository(BaseAutomationRepository):
    """Thread-safe in-memory automation storage."""

    def __init__(self) -> None:
        self._automations: dict[str, Automation] = {}
        self._lock = Lock()

    def save(self, automation: Automation) -> None:
        with self._lock:
            self._automations[automation.automation_id] = automation.model_copy(deep=True)

    def get_by_id(self, automation_id: str) -> Automation | None:
        with self._lock:
            item = self._automations.get(automation_id)
            return item.model_copy(deep=True) if item else None

    def list(
        self,
        owner_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Automation]:
        with self._lock:
            results = list(self._automations.values())

        if owner_id:
            results = [a for a in results if a.owner_id == owner_id]
        if status:
            results = [a for a in results if a.status.value == status or a.status == status]

        return [a.model_copy(deep=True) for a in results[offset : offset + limit]]

    def delete(self, automation_id: str) -> bool:
        with self._lock:
            return self._automations.pop(automation_id, None) is not None


class MemoryExecutionRepository(BaseExecutionRepository):
    """Thread-safe in-memory execution history storage."""

    def __init__(self) -> None:
        self._executions: dict[str, Execution] = {}
        self._idempotency_map: dict[str, str] = {}
        self._lock = Lock()

    def save(self, execution: Execution) -> None:
        with self._lock:
            self._executions[execution.execution_id] = execution.model_copy(deep=True)
            if execution.idempotency_key:
                self._idempotency_map[execution.idempotency_key] = execution.execution_id

    def get_by_id(self, execution_id: str) -> Execution | None:
        with self._lock:
            item = self._executions.get(execution_id)
            return item.model_copy(deep=True) if item else None

    def get_by_idempotency_key(self, key: str) -> Execution | None:
        with self._lock:
            exc_id = self._idempotency_map.get(key)
            if not exc_id:
                return None
            item = self._executions.get(exc_id)
            return item.model_copy(deep=True) if item else None

    def list(
        self,
        automation_id: str | None = None,
        schedule_id: str | None = None,
        owner_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Execution]:
        with self._lock:
            results = list(self._executions.values())

        if automation_id:
            results = [e for e in results if e.automation_id == automation_id]
        if schedule_id:
            results = [e for e in results if e.schedule_id == schedule_id]
        if owner_id:
            results = [e for e in results if e.owner_id == owner_id]
        if status:
            results = [e for e in results if e.status.value == status or e.status == status]

        results.sort(key=lambda x: x.started_at, reverse=True)
        return [e.model_copy(deep=True) for e in results[offset : offset + limit]]

    def count_active_executions(
        self, automation_id: str | None = None, owner_id: str | None = None
    ) -> int:
        with self._lock:
            count = 0
            for e in self._executions.values():
                if e.status.value in ("RUNNING", "PENDING", "PAUSED"):
                    if automation_id and e.automation_id != automation_id:
                        continue
                    if owner_id and e.owner_id != owner_id:
                        continue
                    count += 1
            return count


class MemoryTriggerRepository(BaseTriggerRepository):
    """Thread-safe in-memory trigger storage."""

    def __init__(self) -> None:
        self._triggers: dict[str, Trigger] = {}
        self._lock = Lock()

    def save(self, trigger: Trigger) -> None:
        with self._lock:
            self._triggers[trigger.trigger_id] = trigger.model_copy(deep=True)

    def get_by_id(self, trigger_id: str) -> Trigger | None:
        with self._lock:
            item = self._triggers.get(trigger_id)
            return item.model_copy(deep=True) if item else None

    def list(self, trigger_type: str | None = None, status: str | None = None) -> list[Trigger]:
        with self._lock:
            results = list(self._triggers.values())

        if trigger_type:
            results = [
                t for t in results if t.trigger_type.value == trigger_type or t.trigger_type == trigger_type
            ]
        if status:
            results = [t for t in results if t.status.value == status or t.status == status]

        return [t.model_copy(deep=True) for t in results]


class MemorySchedulerLockRepository(BaseSchedulerLockRepository):
    """Thread-safe in-memory lock storage with expiration cleanup."""

    def __init__(self) -> None:
        self._locks: dict[str, SchedulerLock] = {}
        self._lock = Lock()

    def acquire(self, resource_id: str, owner_id: str, timeout_seconds: float) -> bool:
        now = datetime.now(UTC)
        with self._lock:
            existing = self._locks.get(resource_id)
            if existing:
                exp = existing.expires_at
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=UTC)
                if exp > now:
                    if existing.owner_id == owner_id:
                        # Extend lock
                        existing.expires_at = now + datetime.resolution * 0 + (
                            datetime.fromtimestamp(now.timestamp() + timeout_seconds, tz=UTC)
                            - datetime.fromtimestamp(now.timestamp(), tz=UTC)
                        )
                        return True
                    return False

            # Acquire new lock
            expires_at = datetime.fromtimestamp(now.timestamp() + timeout_seconds, tz=UTC)
            lock_obj = SchedulerLock(
                resource_id=resource_id,
                owner_id=owner_id,
                acquired_at=now,
                expires_at=expires_at,
            )
            self._locks[resource_id] = lock_obj
            return True

    def release(self, resource_id: str, owner_id: str) -> bool:
        with self._lock:
            existing = self._locks.get(resource_id)
            if existing and existing.owner_id == owner_id:
                del self._locks[resource_id]
                return True
            return False

    def is_locked(self, resource_id: str) -> bool:
        now = datetime.now(UTC)
        with self._lock:
            existing = self._locks.get(resource_id)
            if not existing:
                return False
            exp = existing.expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=UTC)
            return exp > now


class MemoryAuditRepository(BaseAuditRepository):
    """Thread-safe in-memory audit log repository."""

    def __init__(self) -> None:
        self._events: list[SchedulerAuditEvent] = []
        self._lock = Lock()

    def save(self, audit_event: SchedulerAuditEvent) -> None:
        with self._lock:
            self._events.append(audit_event.model_copy(deep=True))

    def list(
        self,
        schedule_id: str | None = None,
        automation_id: str | None = None,
        execution_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SchedulerAuditEvent]:
        with self._lock:
            results = list(self._events)

        if schedule_id:
            results = [e for e in results if e.schedule_id == schedule_id]
        if automation_id:
            results = [e for e in results if e.automation_id == automation_id]
        if execution_id:
            results = [e for e in results if e.execution_id == execution_id]

        results.sort(key=lambda x: x.timestamp, reverse=True)
        return [e.model_copy(deep=True) for e in results[offset : offset + limit]]
