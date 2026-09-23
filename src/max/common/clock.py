"""Clock and time abstraction interface for deterministic time handling."""

from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    """Protocol interface for retrieving UTC timestamps."""

    def now(self) -> datetime:
        """Return current datetime in UTC."""
        ...


class SystemClock:
    """Standard system clock providing actual current UTC time."""

    def now(self) -> datetime:
        """Return real current UTC timestamp."""
        return datetime.now(UTC)


class DeterministicClock:
    """Deterministic test clock for reproducible unit tests and expiration simulations."""

    def __init__(self, initial_time: datetime | None = None) -> None:
        self._current_time = initial_time or datetime.now(UTC)

    def now(self) -> datetime:
        """Return current fixed test timestamp."""
        return self._current_time

    def set_time(self, new_time: datetime) -> None:
        """Explicitly set current test timestamp."""
        if new_time.tzinfo is None:
            new_time = new_time.replace(tzinfo=UTC)
        self._current_time = new_time

    def advance(
        self, seconds: float = 0, minutes: float = 0, hours: float = 0, days: float = 0
    ) -> None:
        """Advance test clock by specified duration."""
        from datetime import timedelta

        delta = timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)
        self._current_time += delta
