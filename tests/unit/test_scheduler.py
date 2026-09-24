"""Comprehensive unit tests for Module 28 — Scheduler & Automation Engine."""

from datetime import UTC, datetime, timedelta

import pytest

from max.scheduler.container import SchedulerContainer, reset_scheduler_container
from max.scheduler.domain.enums import (
    AutomationStatus,
    ConcurrencyPolicy,
    ConditionOperator,
    ExecutionStatus,
    MisfirePolicy,
    ScheduleStatus,
    ScheduleType,
    StepType,
    TriggerType,
)
from max.scheduler.domain.exceptions import (
    CircularDependencyError,
    InvalidStateTransitionError,
)
from max.scheduler.domain.models import (
    Automation,
    AutomationCondition,
    AutomationDefinition,
    AutomationStep,
    Schedule,
    ScheduleEvent,
    Trigger,
    TriggerDefinition,
)
from max.scheduler.domain.state_machine import (
    validate_automation_transition,
    validate_schedule_transition,
)
from max.scheduler.recurrence.cron_parser import CronExpression
from max.scheduler.recurrence.engine import RecurrenceEngine
from max.scheduler.triggers.evaluator import (
    MasterTriggerEvaluator,
    evaluate_condition,
)


@pytest.fixture(autouse=True)
def clean_scheduler_container():
    reset_scheduler_container()
    yield
    reset_scheduler_container()


def test_schedule_state_machine():
    """Test deterministic state machine transitions for ScheduleStatus."""
    # Valid transitions
    validate_schedule_transition(ScheduleStatus.DRAFT, ScheduleStatus.SCHEDULED)
    validate_schedule_transition(ScheduleStatus.SCHEDULED, ScheduleStatus.READY)
    validate_schedule_transition(ScheduleStatus.READY, ScheduleStatus.RUNNING)
    validate_schedule_transition(ScheduleStatus.RUNNING, ScheduleStatus.COMPLETED)
    validate_schedule_transition(ScheduleStatus.RUNNING, ScheduleStatus.FAILED)
    validate_schedule_transition(ScheduleStatus.FAILED, ScheduleStatus.SCHEDULED)

    # Invalid transitions
    with pytest.raises(InvalidStateTransitionError):
        validate_schedule_transition(ScheduleStatus.DRAFT, ScheduleStatus.RUNNING)
    with pytest.raises(InvalidStateTransitionError):
        validate_schedule_transition(ScheduleStatus.COMPLETED, ScheduleStatus.RUNNING)


def test_automation_state_machine():
    """Test state machine transitions for AutomationStatus."""
    validate_automation_transition(AutomationStatus.DRAFT, AutomationStatus.SCHEDULED)
    validate_automation_transition(AutomationStatus.SCHEDULED, AutomationStatus.READY)
    validate_automation_transition(AutomationStatus.READY, AutomationStatus.RUNNING)

    with pytest.raises(InvalidStateTransitionError):
        validate_automation_transition(AutomationStatus.COMPLETED, AutomationStatus.RUNNING)


def test_cron_parsing_and_evaluation():
    """Test standard 5-part cron parser and next occurrence calculation."""
    # Every weekday at 09:00
    cron = CronExpression("0 9 * * 1-5")
    assert cron.matches(datetime(2026, 9, 28, 9, 0, tzinfo=UTC))  # Mon 09:00
    assert not cron.matches(datetime(2026, 9, 27, 9, 0, tzinfo=UTC))  # Sun 09:00

    from_time = datetime(2026, 9, 25, 10, 0, tzinfo=UTC)  # Fri 10:00
    next_run = cron.get_next_occurrence(from_time, tz_name="UTC")
    # Next should be Monday Sep 28 09:00
    assert next_run.weekday() == 0  # Monday
    assert next_run.hour == 9
    assert next_run.minute == 0


def test_recurrence_engine_timezones():
    """Test RecurrenceEngine with IANA timezones."""
    sch = Schedule(
        schedule_type=ScheduleType.CRON,
        cron_expression="0 9 * * *",
        timezone="Asia/Kolkata",
    )
    from_time = datetime(2026, 9, 24, 0, 0, tzinfo=UTC)
    next_run = RecurrenceEngine.get_next_run_time(sch, from_time=from_time)
    assert next_run is not None
    # 09:00 Asia/Kolkata is 03:30 UTC
    assert next_run > from_time


def test_safe_condition_evaluation_no_eval():
    """Test condition evaluator using structured operators (no eval/exec)."""
    ctx = {"system": {"cpu_percent": 85.5, "status": "WARN"}}

    cond_gt = AutomationCondition(
        condition_type="SYSTEM",
        operator=ConditionOperator.GREATER_THAN,
        expected_value=80.0,
        actual_value_path="system.cpu_percent",
    )
    assert evaluate_condition(cond_gt, ctx) is True

    cond_eq = AutomationCondition(
        condition_type="SYSTEM",
        operator=ConditionOperator.EQUALS,
        expected_value="CRITICAL",
        actual_value_path="system.status",
    )
    assert evaluate_condition(cond_eq, ctx) is False


def test_event_trigger_evaluation():
    """Test event trigger evaluation against incoming ScheduleEvent."""
    trg = Trigger(
        trigger_type=TriggerType.EVENT_TRIGGER,
        definition=TriggerDefinition(event_type="github.pull_request.created"),
        condition=AutomationCondition(
            operator=ConditionOperator.EQUALS,
            expected_value="main",
            actual_value_path="base_branch",
        ),
    )

    event_matching = ScheduleEvent(
        event_type="github.pull_request.created",
        source="github",
        payload={"base_branch": "main", "pr_number": 42},
    )

    evaluator = MasterTriggerEvaluator()
    res = evaluator.evaluate(trg, event=event_matching)
    assert res.triggered is True

    event_unmatching = ScheduleEvent(
        event_type="github.pull_request.created",
        source="github",
        payload={"base_branch": "dev", "pr_number": 43},
    )
    res_unmatch = evaluator.evaluate(trg, event=event_unmatching)
    assert res_unmatch.triggered is False


def test_circular_dependency_detection():
    """Test that circular automation dependencies are detected and rejected."""
    container = SchedulerContainer()
    aut1 = Automation(automation_id="aut_1", name="Automation 1", dependencies=["aut_2"])
    aut2 = Automation(automation_id="aut_2", name="Automation 2", dependencies=["aut_1"])

    container.automation_engine.automation_repo.save(aut1)

    with pytest.raises(CircularDependencyError):
        container.automation_engine.create_automation(aut2)


def test_misfire_policy_skip():
    """Test MisfirePolicy.SKIP behavior."""
    container = SchedulerContainer()
    now = datetime.now(UTC)
    past_time = now - timedelta(hours=2)

    sch = Schedule(
        schedule_id="sch_misfire",
        schedule_type=ScheduleType.INTERVAL,
        interval_seconds=3600.0,
        next_run_at=past_time,
        misfire_policy=MisfirePolicy.SKIP,
        automation_id="aut_dummy",
    )
    container.scheduler_service.schedule_repo.save(sch)

    # Executing due schedules at `now` should skip past execution and advance next_run_at
    execs = container.scheduler_service.execute_due(current_time=now)
    assert len(execs) == 0  # Skipped execution

    updated_sch = container.scheduler_service.schedule_repo.get_by_id("sch_misfire")
    assert updated_sch.next_run_at > now


def test_concurrency_policy_forbid():
    """Test ConcurrencyPolicy.FORBID blocks overlapping execution."""
    container = SchedulerContainer()
    now = datetime.now(UTC)

    aut = Automation(
        automation_id="aut_concurrency",
        name="Concurrent Test",
        definition=AutomationDefinition(
            steps=[AutomationStep(step_type=StepType.CREATE_TASK, configuration={"task_name": "Job"})]
        ),
    )
    container.automation_engine.create_automation(aut)

    sch = Schedule(
        schedule_id="sch_concurrency",
        schedule_type=ScheduleType.INTERVAL,
        interval_seconds=60.0,
        next_run_at=now,
        concurrency_policy=ConcurrencyPolicy.FORBID,
        automation_id="aut_concurrency",
    )
    container.scheduler_service.schedule_repo.save(sch)

    # Mark an existing active execution for aut_concurrency
    container.automation_engine.execution_repo.save(
        container.automation_engine.execute_automation("aut_concurrency", dry_run=True)
    )
    # Re-save as RUNNING
    exc = container.automation_engine.execution_repo.list(automation_id="aut_concurrency")[0]
    exc.status = ExecutionStatus.RUNNING
    container.automation_engine.execution_repo.save(exc)

    execs = container.scheduler_service.execute_due(current_time=now)
    assert len(execs) == 0  # Blocked by FORBID policy


def test_dry_run_automation():
    """Test dry run execution plan generation without side effects."""
    container = SchedulerContainer()
    aut = Automation(
        automation_id="aut_dry",
        name="Dry Run Test",
        definition=AutomationDefinition(
            steps=[
                AutomationStep(step_type=StepType.CREATE_TASK, configuration={"task_name": "Report Task"}),
                AutomationStep(step_type=StepType.SEND_NOTIFICATION, configuration={"title": "Notify User"}),
            ]
        ),
    )
    container.automation_engine.create_automation(aut)

    exc = container.automation_engine.execute_automation("aut_dry", dry_run=True)
    assert exc.status == ExecutionStatus.COMPLETED
    assert exc.result.get("dry_run") is True
    plan = exc.result.get("plan", {})
    assert plan.get("total_steps") == 2
    assert len(plan.get("steps")) == 2
