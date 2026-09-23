"""Unit tests for Module 13 Agent Engine domain models and state machine."""

import pytest
from pydantic import ValidationError

from max.agents.domain.agent import (
    Agent,
    AgentCapability,
    AgentConfiguration,
    AgentLimits,
)
from max.agents.domain.assignment import AgentAssignment, AssignmentPriority, AssignmentStatus
from max.agents.domain.enums import AgentRole, AgentStatus, AgentType
from max.agents.domain.exceptions import (
    InvalidAgentStateTransitionError,
    InvalidRunStateTransitionError,
)
from max.agents.domain.run import (
    AgentFailure,
    AgentRetryPolicy,
    AgentRunStatus,
    RetryBackoffStrategy,
)
from max.agents.domain.trace import AgentEvent, AgentEventType, AgentTrace
from max.agents.services.capability_matcher import CapabilityMatcher
from max.agents.services.state_machine import AgentStateMachine


def test_agent_creation_defaults() -> None:
    """Verify default values when instantiating an Agent entity."""
    agent = Agent(name="planner_agent", owner_id="user_123")

    assert agent.id.startswith("agent_")
    assert agent.name == "planner_agent"
    assert agent.type == AgentType.GENERAL
    assert agent.role == AgentRole.ASSISTANT
    assert agent.status == AgentStatus.CREATED
    assert agent.owner_id == "user_123"
    assert isinstance(agent.configuration, AgentConfiguration)
    assert isinstance(agent.limits, AgentLimits)


def test_agent_limits_validation() -> None:
    """Verify validation checks on AgentLimits."""
    limits = AgentLimits(max_tasks_per_run=5, max_steps_per_run=10)
    assert limits.max_tasks_per_run == 5

    with pytest.raises(ValidationError):
        AgentLimits(max_tasks_per_run=0)

    with pytest.raises(ValidationError):
        AgentLimits(max_agent_depth=0)


def test_agent_state_machine_transitions() -> None:
    """Verify valid and invalid state transitions for Agent lifecycle."""
    # Valid transitions
    assert AgentStateMachine.can_transition(AgentStatus.CREATED, AgentStatus.ACTIVE)
    assert AgentStateMachine.can_transition(AgentStatus.ACTIVE, AgentStatus.PAUSED)
    assert AgentStateMachine.can_transition(AgentStatus.PAUSED, AgentStatus.ACTIVE)
    assert AgentStateMachine.can_transition(AgentStatus.ACTIVE, AgentStatus.DISABLED)
    assert AgentStateMachine.can_transition(AgentStatus.DISABLED, AgentStatus.ARCHIVED)

    # Invalid transitions
    with pytest.raises(InvalidAgentStateTransitionError):
        AgentStateMachine.validate_agent_transition(AgentStatus.ARCHIVED, AgentStatus.ACTIVE)

    with pytest.raises(InvalidAgentStateTransitionError):
        AgentStateMachine.validate_agent_transition(AgentStatus.CREATED, AgentStatus.PAUSED)


def test_agent_run_state_machine_transitions() -> None:
    """Verify valid and invalid state transitions for AgentRun lifecycle."""
    # Valid
    assert AgentStateMachine.can_transition_run(AgentRunStatus.CREATED, AgentRunStatus.INITIALIZING)
    assert AgentStateMachine.can_transition_run(AgentRunStatus.INITIALIZING, AgentRunStatus.READY)
    assert AgentStateMachine.can_transition_run(AgentRunStatus.READY, AgentRunStatus.RUNNING)
    assert AgentStateMachine.can_transition_run(AgentRunStatus.RUNNING, AgentRunStatus.COMPLETED)
    assert AgentStateMachine.can_transition_run(AgentRunStatus.RUNNING, AgentRunStatus.FAILED)
    assert AgentStateMachine.can_transition_run(AgentRunStatus.RUNNING, AgentRunStatus.WAITING)
    assert AgentStateMachine.can_transition_run(AgentRunStatus.WAITING, AgentRunStatus.RUNNING)

    # Invalid
    with pytest.raises(InvalidRunStateTransitionError):
        AgentStateMachine.validate_run_transition(AgentRunStatus.COMPLETED, AgentRunStatus.RUNNING)

    with pytest.raises(InvalidRunStateTransitionError):
        AgentStateMachine.validate_run_transition(AgentRunStatus.CREATED, AgentRunStatus.RUNNING)


def test_capability_matcher() -> None:
    """Verify exact, partial, and missing capability matching logic."""
    agent_caps = [AgentCapability.PLANNING, AgentCapability.TASK_COORDINATION]

    res_exact = CapabilityMatcher.match(
        required=[AgentCapability.PLANNING, AgentCapability.TASK_COORDINATION],
        available=agent_caps,
    )
    assert res_exact.matched is True
    assert len(res_exact.missing_capabilities) == 0

    res_missing = CapabilityMatcher.match(
        required=[AgentCapability.PLANNING, AgentCapability.CODE_REVIEW],
        available=agent_caps,
    )
    assert res_missing.matched is False
    assert AgentCapability.CODE_REVIEW in res_missing.missing_capabilities


def test_assignment_model() -> None:
    """Verify AgentAssignment instantiation and default properties."""
    assignment = AgentAssignment(
        agent_id="agent_1",
        task_id="task_1",
        priority=AssignmentPriority.HIGH,
    )
    assert assignment.assignment_id.startswith("asgn_")
    assert assignment.status == AssignmentStatus.ASSIGNED
    assert assignment.priority == AssignmentPriority.HIGH


def test_retry_policy_and_run_failure() -> None:
    """Verify AgentRetryPolicy backoff calculation and AgentFailure."""
    policy = AgentRetryPolicy(
        max_retries=3,
        backoff_strategy=RetryBackoffStrategy.EXPONENTIAL,
        initial_delay_seconds=1.0,
        max_delay_seconds=10.0,
    )
    assert policy.calculate_delay(1) == 1.0
    assert policy.calculate_delay(2) == 2.0
    assert policy.calculate_delay(3) == 4.0
    assert policy.should_retry(retry_count=2, failure_category="MODEL_ERROR") is True
    assert policy.should_retry(retry_count=3, failure_category="MODEL_ERROR") is False

    failure = AgentFailure(
        error_code="MODEL_TIMEOUT",
        message="Model response timed out",
        category="TIMEOUT",
        retryable=True,
    )
    assert failure.category == "TIMEOUT"
    assert failure.retryable is True


def test_agent_trace_and_events() -> None:
    """Verify AgentTrace event recording without storing sensitive chain-of-thought."""
    trace = AgentTrace(run_id="run_123", agent_id="agent_1")
    event = AgentEvent(
        event_type=AgentEventType.RUN_STARTED,
        agent_id="agent_1",
        run_id="run_123",
        summary="Execution run started",
    )
    trace.record_event(event)

    assert len(trace.events) == 1
    assert trace.events[0].event_type == AgentEventType.RUN_STARTED
    assert trace.events[0].summary == "Execution run started"
