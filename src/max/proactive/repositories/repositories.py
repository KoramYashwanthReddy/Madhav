"""Repositories for Module 30 — Proactive Intelligence Engine."""

from abc import ABC, abstractmethod
from datetime import UTC
from typing import Any

from max.proactive.domain.models import (
    ProactiveAction,
    ProactiveCandidate,
    ProactiveDecision,
    ProactiveFeedback,
    ProactiveOutcome,
    ProactiveRule,
    ProactiveSignal,
)


class SignalRepository(ABC):
    """Abstract interface for proactive signal storage."""

    @abstractmethod
    async def save_signal(self, signal: ProactiveSignal) -> ProactiveSignal: ...

    @abstractmethod
    async def get_signal(self, signal_id: str, owner_id: str) -> ProactiveSignal | None: ...

    @abstractmethod
    async def list_signals(self, owner_id: str, limit: int = 100) -> list[ProactiveSignal]: ...


class InMemorySignalRepository(SignalRepository):
    """In-memory implementation of SignalRepository."""

    def __init__(self) -> None:
        self._signals: dict[str, ProactiveSignal] = {}

    async def save_signal(self, signal: ProactiveSignal) -> ProactiveSignal:
        self._signals[signal.signal_id] = signal
        return signal

    async def get_signal(self, signal_id: str, owner_id: str) -> ProactiveSignal | None:
        sig = self._signals.get(signal_id)
        if sig and sig.owner_id == owner_id:
            return sig
        return None

    async def list_signals(self, owner_id: str, limit: int = 100) -> list[ProactiveSignal]:
        res = [s for s in self._signals.values() if s.owner_id == owner_id]
        res.sort(key=lambda s: s.received_at, reverse=True)
        return res[:limit]


class CandidateRepository(ABC):
    """Abstract interface for proactive candidate storage."""

    @abstractmethod
    async def save_candidate(self, candidate: ProactiveCandidate) -> ProactiveCandidate: ...

    @abstractmethod
    async def get_candidate(self, candidate_id: str, owner_id: str) -> ProactiveCandidate | None: ...

    @abstractmethod
    async def list_candidates(
        self, owner_id: str, limit: int = 100
    ) -> list[ProactiveCandidate]: ...

    @abstractmethod
    async def find_recent_similar(
        self, owner_id: str, key: str, window_seconds: float, exclude_candidate_id: str | None = None
    ) -> list[ProactiveCandidate]: ...


class InMemoryCandidateRepository(CandidateRepository):
    """In-memory implementation of CandidateRepository."""

    def __init__(self) -> None:
        self._candidates: dict[str, ProactiveCandidate] = {}

    async def save_candidate(self, candidate: ProactiveCandidate) -> ProactiveCandidate:
        self._candidates[candidate.candidate_id] = candidate
        return candidate

    async def get_candidate(self, candidate_id: str, owner_id: str) -> ProactiveCandidate | None:
        cand = self._candidates.get(candidate_id)
        if cand and cand.owner_id == owner_id:
            return cand
        return None

    async def list_candidates(
        self, owner_id: str, limit: int = 100
    ) -> list[ProactiveCandidate]:
        res = [c for c in self._candidates.values() if c.owner_id == owner_id]
        res.sort(key=lambda c: c.created_at, reverse=True)
        return res[:limit]

    async def find_recent_similar(
        self, owner_id: str, key: str, window_seconds: float, exclude_candidate_id: str | None = None
    ) -> list[ProactiveCandidate]:
        from datetime import datetime
        now = datetime.now(UTC)
        results: list[ProactiveCandidate] = []
        for cand in self._candidates.values():
            if exclude_candidate_id and cand.candidate_id == exclude_candidate_id:
                continue
            if cand.owner_id == owner_id and cand.deduplication_key == key:
                age = (now - cand.created_at).total_seconds()
                if age <= window_seconds:
                    results.append(cand)
        return results


class DecisionRepository(ABC):
    """Abstract interface for proactive decision storage."""

    @abstractmethod
    async def save_decision(self, decision: ProactiveDecision) -> ProactiveDecision: ...

    @abstractmethod
    async def get_decision(self, decision_id: str, owner_id: str) -> ProactiveDecision | None: ...

    @abstractmethod
    async def list_decisions(self, owner_id: str, limit: int = 100) -> list[ProactiveDecision]: ...

    @abstractmethod
    async def find_recent_decisions(
        self, owner_id: str, window_seconds: float
    ) -> list[ProactiveDecision]: ...


class InMemoryDecisionRepository(DecisionRepository):
    """In-memory implementation of DecisionRepository."""

    def __init__(self) -> None:
        self._decisions: dict[str, ProactiveDecision] = {}

    async def save_decision(self, decision: ProactiveDecision) -> ProactiveDecision:
        self._decisions[decision.decision_id] = decision
        return decision

    async def get_decision(self, decision_id: str, owner_id: str) -> ProactiveDecision | None:
        dec = self._decisions.get(decision_id)
        if dec and dec.owner_id == owner_id:
            return dec
        return None

    async def list_decisions(self, owner_id: str, limit: int = 100) -> list[ProactiveDecision]:
        res = [d for d in self._decisions.values() if d.owner_id == owner_id]
        res.sort(key=lambda d: d.created_at, reverse=True)
        return res[:limit]

    async def find_recent_decisions(
        self, owner_id: str, window_seconds: float
    ) -> list[ProactiveDecision]:
        from datetime import datetime
        now = datetime.now(UTC)
        results: list[ProactiveDecision] = []
        for dec in self._decisions.values():
            if dec.owner_id == owner_id:
                age = (now - dec.created_at).total_seconds()
                if age <= window_seconds:
                    results.append(dec)
        return results


class ActionRepository(ABC):
    """Abstract interface for proactive action storage."""

    @abstractmethod
    async def save_action(self, action: ProactiveAction) -> ProactiveAction: ...

    @abstractmethod
    async def get_action(self, action_id: str, owner_id: str) -> ProactiveAction | None: ...

    @abstractmethod
    async def list_actions(self, owner_id: str, limit: int = 100) -> list[ProactiveAction]: ...


class InMemoryActionRepository(ActionRepository):
    """In-memory implementation of ActionRepository."""

    def __init__(self) -> None:
        self._actions: dict[str, ProactiveAction] = {}

    async def save_action(self, action: ProactiveAction) -> ProactiveAction:
        self._actions[action.action_id] = action
        return action

    async def get_action(self, action_id: str, owner_id: str) -> ProactiveAction | None:
        act = self._actions.get(action_id)
        if act and act.owner_id == owner_id:
            return act
        return None

    async def list_actions(self, owner_id: str, limit: int = 100) -> list[ProactiveAction]:
        res = [a for a in self._actions.values() if a.owner_id == owner_id]
        res.sort(key=lambda a: a.created_at, reverse=True)
        return res[:limit]


class OutcomeRepository(ABC):
    """Abstract interface for proactive outcome storage."""

    @abstractmethod
    async def save_outcome(self, outcome: ProactiveOutcome) -> ProactiveOutcome: ...

    @abstractmethod
    async def get_outcome(self, outcome_id: str, owner_id: str) -> ProactiveOutcome | None: ...


class InMemoryOutcomeRepository(OutcomeRepository):
    """In-memory implementation of OutcomeRepository."""

    def __init__(self) -> None:
        self._outcomes: dict[str, ProactiveOutcome] = {}

    async def save_outcome(self, outcome: ProactiveOutcome) -> ProactiveOutcome:
        self._outcomes[outcome.outcome_id] = outcome
        return outcome

    async def get_outcome(self, outcome_id: str, owner_id: str) -> ProactiveOutcome | None:
        out = self._outcomes.get(outcome_id)
        if out and out.owner_id == owner_id:
            return out
        return None


class FeedbackRepository(ABC):
    """Abstract interface for user feedback storage."""

    @abstractmethod
    async def save_feedback(self, feedback: ProactiveFeedback) -> ProactiveFeedback: ...

    @abstractmethod
    async def list_feedback(self, owner_id: str, limit: int = 100) -> list[ProactiveFeedback]: ...


class InMemoryFeedbackRepository(FeedbackRepository):
    """In-memory implementation of FeedbackRepository."""

    def __init__(self) -> None:
        self._feedback: list[ProactiveFeedback] = []

    async def save_feedback(self, feedback: ProactiveFeedback) -> ProactiveFeedback:
        self._feedback.append(feedback)
        return feedback

    async def list_feedback(self, owner_id: str, limit: int = 100) -> list[ProactiveFeedback]:
        res = [f for f in self._feedback if f.owner_id == owner_id]
        res.sort(key=lambda f: f.created_at, reverse=True)
        return res[:limit]


class ProactiveRuleRepository(ABC):
    """Abstract interface for proactive rule storage."""

    @abstractmethod
    async def save_rule(self, rule: ProactiveRule) -> ProactiveRule: ...

    @abstractmethod
    async def get_rule(self, rule_id: str, owner_id: str) -> ProactiveRule | None: ...

    @abstractmethod
    async def list_rules(self, owner_id: str, limit: int = 100) -> list[ProactiveRule]: ...


class InMemoryProactiveRuleRepository(ProactiveRuleRepository):
    """In-memory implementation of ProactiveRuleRepository."""

    def __init__(self) -> None:
        self._rules: dict[str, ProactiveRule] = {}

    async def save_rule(self, rule: ProactiveRule) -> ProactiveRule:
        self._rules[rule.rule_id] = rule
        return rule

    async def get_rule(self, rule_id: str, owner_id: str) -> ProactiveRule | None:
        r = self._rules.get(rule_id)
        if r and r.owner_id == owner_id:
            return r
        return None

    async def list_rules(self, owner_id: str, limit: int = 100) -> list[ProactiveRule]:
        res = [r for r in self._rules.values() if r.owner_id == owner_id]
        res.sort(key=lambda r: r.updated_at, reverse=True)
        return res[:limit]


class AuditRepository(ABC):
    """Abstract interface for proactive audit log entry storage."""

    @abstractmethod
    async def record_event(
        self, owner_id: str, event_type: str, details: dict[str, Any]
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def list_events(self, owner_id: str, limit: int = 100) -> list[dict[str, Any]]: ...


class InMemoryAuditRepository(AuditRepository):
    """In-memory implementation of AuditRepository."""

    def __init__(self) -> None:
        self._logs: list[dict[str, Any]] = []

    async def record_event(
        self, owner_id: str, event_type: str, details: dict[str, Any]
    ) -> dict[str, Any]:
        from datetime import datetime
        entry = {
            "owner_id": owner_id,
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self._logs.append(entry)
        return entry

    async def list_events(self, owner_id: str, limit: int = 100) -> list[dict[str, Any]]:
        res = [entry for entry in self._logs if entry["owner_id"] == owner_id]
        return res[-limit:]
