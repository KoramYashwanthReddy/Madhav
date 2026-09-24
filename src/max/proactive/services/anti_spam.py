"""Anti-spam, deduplication, attention budget, and circuit breaker services for Module 30."""

import logging
from datetime import UTC, datetime

from max.config.sections import ProactiveSettings
from max.proactive.domain.exceptions import AttentionBudgetExceededError
from max.proactive.domain.models import AttentionBudget, ProactiveCandidate
from max.proactive.repositories.repositories import CandidateRepository, DecisionRepository

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ProactiveDeduplicationService:
    """Manages signal, candidate, and notification deduplication and cooldown windows."""

    def __init__(
        self,
        candidate_repo: CandidateRepository,
        decision_repo: DecisionRepository,
        default_cooldown_seconds: float = 14400.0,
    ) -> None:
        self._candidate_repo = candidate_repo
        self._decision_repo = decision_repo
        self._default_cooldown = default_cooldown_seconds
        self._recent_keys: dict[str, float] = {}  # key -> timestamp

    def build_deduplication_key(
        self, owner_id: str, category: str, signal_type: str, item_id: str
    ) -> str:
        return f"{owner_id}:{category}:{signal_type}:{item_id}"

    async def is_duplicate_candidate(
        self, candidate: ProactiveCandidate, cooldown_seconds: float | None = None
    ) -> tuple[bool, str]:
        """Check whether candidate is a duplicate within cooldown period."""
        cooldown = cooldown_seconds if cooldown_seconds is not None else self._default_cooldown
        if not candidate.deduplication_key:
            return False, "No deduplication key set"

        recent = await self._candidate_repo.find_recent_similar(
            owner_id=candidate.owner_id,
            key=candidate.deduplication_key,
            window_seconds=cooldown,
            exclude_candidate_id=candidate.candidate_id,
        )
        if recent:
            return True, f"Duplicate candidate found within {cooldown}s cooldown window"

        return False, "Not a duplicate"


class AttentionBudgetService:
    """Tracks and enforces user attention budget limits to prevent notification spam."""

    def __init__(self, settings: ProactiveSettings) -> None:
        self._settings = settings
        self._budgets: dict[str, AttentionBudget] = {}  # user_id -> AttentionBudget

    def get_budget(self, user_id: str = "default_owner") -> AttentionBudget:
        now = _utc_now()
        current_hour = now.hour
        current_day = now.timetuple().tm_yday

        if user_id not in self._budgets:
            self._budgets[user_id] = AttentionBudget(
                user_id=user_id,
                hourly_count=0,
                daily_count=0,
                last_reset_hour=current_hour,
                last_reset_day=current_day,
                max_per_hour=self._settings.max_notifications_per_hour,
                max_per_day=self._settings.max_notifications_per_day,
            )

        budget = self._budgets[user_id]

        # Reset hourly window if hour changed
        if budget.last_reset_hour != current_hour:
            budget.hourly_count = 0
            budget.last_reset_hour = current_hour

        # Reset daily window if day changed
        if budget.last_reset_day != current_day:
            budget.daily_count = 0
            budget.last_reset_day = current_day

        return budget

    def can_consume_budget(self, user_id: str = "default_owner") -> tuple[bool, str]:
        budget = self.get_budget(user_id)
        if budget.hourly_count >= budget.max_per_hour:
            return False, f"Hourly attention budget exceeded ({budget.hourly_count}/{budget.max_per_hour})"
        if budget.daily_count >= budget.max_per_day:
            return False, f"Daily attention budget exceeded ({budget.daily_count}/{budget.max_per_day})"
        return True, "Within attention budget"

    def consume_budget(self, user_id: str = "default_owner") -> None:
        allowed, reason = self.can_consume_budget(user_id)
        if not allowed:
            raise AttentionBudgetExceededError(reason)
        budget = self.get_budget(user_id)
        budget.hourly_count += 1
        budget.daily_count += 1


class CircuitBreakerService:
    """Monitors proactive rule/source failure & false-positive rates to trip circuit breakers."""

    def __init__(self, failure_threshold: int = 5) -> None:
        self._threshold = failure_threshold
        self._failures: dict[str, int] = {}  # rule_id/source -> count
        self._tripped: dict[str, float] = {}  # rule_id/source -> tripped_at_timestamp

    def record_failure(self, identifier: str) -> None:
        self._failures[identifier] = self._failures.get(identifier, 0) + 1
        if self._failures[identifier] >= self._threshold:
            self._tripped[identifier] = _utc_now().timestamp()
            logger.warning("Circuit breaker TRIPPED for %s (failures: %d)", identifier, self._failures[identifier])

    def record_success(self, identifier: str) -> None:
        if identifier in self._failures:
            self._failures[identifier] = max(0, self._failures[identifier] - 1)

    def is_tripped(self, identifier: str) -> bool:
        if identifier in self._tripped:
            # Check if 1 hour has elapsed since trip
            elapsed = _utc_now().timestamp() - self._tripped[identifier]
            if elapsed < 3600.0:
                return True
            else:
                # Reset breaker after 1 hour
                del self._tripped[identifier]
                self._failures[identifier] = 0
        return False
