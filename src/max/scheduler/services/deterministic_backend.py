"""Deterministic Scheduler Backend for controlled development and testing."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from max.scheduler.domain.models import Execution, ScheduleEvent
from max.scheduler.services.scheduler_service import SchedulerService


class DeterministicSchedulerBackend:
    """Provides deterministic time control and manual tick execution for tests."""

    def __init__(self, scheduler_service: SchedulerService) -> None:
        self.scheduler_service = scheduler_service
        self._simulated_time: datetime = datetime.now(UTC)

    def get_current_time(self) -> datetime:
        """Get current simulated time in UTC."""
        return self._simulated_time

    def set_time(self, new_time: datetime) -> datetime:
        """Explicitly set simulated clock time."""
        if new_time.tzinfo is None:
            new_time = new_time.replace(tzinfo=UTC)
        self._simulated_time = new_time
        return self._simulated_time

    def advance_time(self, seconds: float = 0.0, minutes: float = 0.0, hours: float = 0.0, days: float = 0.0) -> datetime:
        """Advance simulated clock by specified duration."""
        delta = timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)
        self._simulated_time += delta
        return self._simulated_time

    def run_due(self) -> list[Execution]:
        """Execute all schedules due at current simulated time."""
        return self.scheduler_service.execute_due(current_time=self._simulated_time)

    def advance_and_run(self, seconds: float = 0.0, minutes: float = 0.0, hours: float = 0.0, days: float = 0.0) -> list[Execution]:
        """Convenience helper: advance simulated time and execute due schedules."""
        self.advance_time(seconds=seconds, minutes=minutes, hours=hours, days=days)
        return self.run_due()

    def emit_event(self, event: ScheduleEvent) -> list[Execution]:
        """Emit an event into the scheduler to trigger matching event-driven automations."""
        return self.scheduler_service.process_event(event)
