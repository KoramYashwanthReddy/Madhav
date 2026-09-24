"""Provider-neutral trigger evaluators and safe condition evaluation engine."""

import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from max.scheduler.domain.enums import ConditionOperator, TriggerType
from max.scheduler.domain.models import AutomationCondition, ScheduleEvent, Trigger


class TriggerResult(BaseModel):
    """Evaluation result for a trigger."""

    triggered: bool
    reason: str = ""
    event_payload: dict[str, Any] = Field(default_factory=dict)


def extract_context_value(context: dict[str, Any], path: str | None) -> Any:
    """Extract nested context value using dot-notation path (e.g., 'payload.user.id')."""
    if not path or not context:
        return context

    current: Any = context
    for key in path.split("."):
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current


def evaluate_condition(condition: AutomationCondition | None, context: dict[str, Any]) -> bool:
    """Evaluate structured condition safely WITHOUT using eval() or exec()."""
    if condition is None:
        return True

    actual_val = (
        extract_context_value(context, condition.actual_value_path)
        if condition.actual_value_path
        else context.get("value")
    )
    expected_val = condition.expected_value
    op = condition.operator

    if op == ConditionOperator.EQUALS:
        return bool(actual_val == expected_val)
    elif op == ConditionOperator.NOT_EQUALS:
        return bool(actual_val != expected_val)
    elif op == ConditionOperator.GREATER_THAN:
        return bool(actual_val is not None and actual_val > expected_val)
    elif op == ConditionOperator.LESS_THAN:
        return bool(actual_val is not None and actual_val < expected_val)
    elif op == ConditionOperator.GREATER_EQUAL:
        return bool(actual_val is not None and actual_val >= expected_val)
    elif op == ConditionOperator.LESS_EQUAL:
        return bool(actual_val is not None and actual_val <= expected_val)
    elif op == ConditionOperator.CONTAINS:
        return bool(actual_val is not None and expected_val in actual_val)
    elif op == ConditionOperator.IN:
        return bool(actual_val is not None and actual_val in expected_val)
    elif op == ConditionOperator.MATCHES_REGEX:
        if actual_val is None or not isinstance(actual_val, str):
            return False
        return bool(re.search(str(expected_val), actual_val))

    return False


class BaseTriggerEvaluator(ABC):
    """Abstract trigger evaluator interface."""

    @abstractmethod
    def evaluate(
        self,
        trigger: Trigger,
        current_time: datetime | None = None,
        event: ScheduleEvent | None = None,
        context: dict[str, Any] | None = None,
    ) -> TriggerResult:
        """Evaluate trigger and return structured result."""
        pass


class TimeTriggerEvaluator(BaseTriggerEvaluator):
    """Evaluates TIME_TRIGGER, INTERVAL_TRIGGER, and CRON_TRIGGER."""

    def evaluate(
        self,
        trigger: Trigger,
        current_time: datetime | None = None,
        event: ScheduleEvent | None = None,
        context: dict[str, Any] | None = None,
    ) -> TriggerResult:
        if trigger.trigger_type not in (
            TriggerType.TIME_TRIGGER,
            TriggerType.INTERVAL_TRIGGER,
            TriggerType.CRON_TRIGGER,
        ):
            return TriggerResult(triggered=False, reason="Mismatched trigger type")

        ctx = context or {}
        cond_passed = evaluate_condition(trigger.condition, ctx)
        if not cond_passed:
            return TriggerResult(triggered=False, reason="Trigger condition evaluated to False")

        return TriggerResult(triggered=True, reason="Time trigger criteria met")


class EventTriggerEvaluator(BaseTriggerEvaluator):
    """Evaluates EVENT_TRIGGER based on incoming system or external events."""

    def evaluate(
        self,
        trigger: Trigger,
        current_time: datetime | None = None,
        event: ScheduleEvent | None = None,
        context: dict[str, Any] | None = None,
    ) -> TriggerResult:
        if trigger.trigger_type != TriggerType.EVENT_TRIGGER:
            return TriggerResult(triggered=False, reason="Not an EVENT_TRIGGER")

        if event is None:
            return TriggerResult(triggered=False, reason="No event provided")

        expected_event_type = trigger.definition.event_type
        if expected_event_type and event.event_type != expected_event_type:
            return TriggerResult(
                triggered=False,
                reason=f"Event type mismatch: expected '{expected_event_type}', got '{event.event_type}'",
            )

        eval_ctx = context.copy() if context else {}
        eval_ctx.update(event.payload)
        eval_ctx["event_type"] = event.event_type
        eval_ctx["event_source"] = event.source

        if not evaluate_condition(trigger.condition, eval_ctx):
            return TriggerResult(triggered=False, reason="Event condition evaluated to False")

        return TriggerResult(
            triggered=True,
            reason=f"Event '{event.event_type}' matched trigger criteria",
            event_payload=event.payload,
        )


class ConditionTriggerEvaluator(BaseTriggerEvaluator):
    """Evaluates CONDITION_TRIGGER based on periodic condition checks."""

    def evaluate(
        self,
        trigger: Trigger,
        current_time: datetime | None = None,
        event: ScheduleEvent | None = None,
        context: dict[str, Any] | None = None,
    ) -> TriggerResult:
        if trigger.trigger_type != TriggerType.CONDITION_TRIGGER:
            return TriggerResult(triggered=False, reason="Not a CONDITION_TRIGGER")

        ctx = context or {}
        cond = trigger.condition or trigger.definition.condition
        if evaluate_condition(cond, ctx):
            return TriggerResult(triggered=True, reason="Condition trigger evaluated to True")

        return TriggerResult(triggered=False, reason="Condition trigger evaluated to False")


class ManualTriggerEvaluator(BaseTriggerEvaluator):
    """Evaluates MANUAL_TRIGGER triggered directly by a user or caller."""

    def evaluate(
        self,
        trigger: Trigger,
        current_time: datetime | None = None,
        event: ScheduleEvent | None = None,
        context: dict[str, Any] | None = None,
    ) -> TriggerResult:
        return TriggerResult(triggered=True, reason="Manual execution requested")


class MasterTriggerEvaluator:
    """Master evaluator delegating trigger evaluation to concrete evaluators."""

    def __init__(self) -> None:
        self._evaluators: dict[TriggerType, BaseTriggerEvaluator] = {
            TriggerType.TIME_TRIGGER: TimeTriggerEvaluator(),
            TriggerType.INTERVAL_TRIGGER: TimeTriggerEvaluator(),
            TriggerType.CRON_TRIGGER: TimeTriggerEvaluator(),
            TriggerType.EVENT_TRIGGER: EventTriggerEvaluator(),
            TriggerType.CONDITION_TRIGGER: ConditionTriggerEvaluator(),
            TriggerType.MANUAL_TRIGGER: ManualTriggerEvaluator(),
        }

    def evaluate(
        self,
        trigger: Trigger,
        current_time: datetime | None = None,
        event: ScheduleEvent | None = None,
        context: dict[str, Any] | None = None,
    ) -> TriggerResult:
        evaluator = self._evaluators.get(trigger.trigger_type)
        if not evaluator:
            return TriggerResult(
                triggered=False, reason=f"Unsupported trigger type '{trigger.trigger_type}'"
            )

        return evaluator.evaluate(trigger, current_time, event, context)
