"""Integration and API tests for Module 28 — Scheduler & Automation Engine."""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from max.main import app
from max.scheduler.container import get_scheduler_container, reset_scheduler_container
from max.scheduler.domain.enums import (
    ScheduleType,
    StepType,
)
from max.scheduler.domain.models import (
    Automation,
    AutomationDefinition,
    AutomationStep,
    Schedule,
    ScheduleEvent,
)


@pytest.fixture(autouse=True)
def clean_scheduler():
    reset_scheduler_container()
    yield
    reset_scheduler_container()


@pytest.fixture
def api_client():
    return TestClient(app)


def test_scheduler_and_automation_api_endpoints(api_client: TestClient):
    """Test REST API endpoints under /api/v1/automations and /api/v1/scheduler."""
    # 1. Create Automation via API
    aut_payload = {
        "name": "Daily Cleanup Automation",
        "description": "Deletes temporary scratch files",
        "owner_id": "test_owner",
        "definition": {
            "steps": [
                {
                    "step_type": "CREATE_TASK",
                    "order": 1,
                    "configuration": {"task_name": "Run Cleanup Script"},
                }
            ]
        },
    }
    resp_aut = api_client.post("/api/v1/automations", json=aut_payload)
    assert resp_aut.status_code == 201
    aut_data = resp_aut.json()
    aut_id = aut_data["automation_id"]
    assert aut_data["name"] == "Daily Cleanup Automation"

    # 2. Create Schedule referencing automation
    sch_payload = {
        "schedule_type": "INTERVAL",
        "interval_seconds": 600.0,
        "automation_id": aut_id,
        "owner_id": "test_owner",
        "timezone": "UTC",
    }
    resp_sch = api_client.post("/api/v1/scheduler", json=sch_payload)
    assert resp_sch.status_code == 201
    sch_data = resp_sch.json()
    sch_id = sch_data["schedule_id"]
    assert sch_data["automation_id"] == aut_id

    # 3. Get next run and status
    resp_next = api_client.get(f"/api/v1/scheduler/{sch_id}/next-run")
    assert resp_next.status_code == 200

    resp_status = api_client.get(f"/api/v1/scheduler/{sch_id}/status")
    assert resp_status.status_code == 200
    assert resp_status.json()["status"] == "SCHEDULED"

    # 4. Dry-run automation
    resp_dry = api_client.post(f"/api/v1/automations/{aut_id}/dry-run")
    assert resp_dry.status_code == 200
    assert resp_dry.json()["total_steps"] == 1

    # 5. Trigger automation
    resp_trg = api_client.post(f"/api/v1/automations/{aut_id}/trigger")
    assert resp_trg.status_code == 200
    assert resp_trg.json()["status"] == "COMPLETED"

    # 6. List executions
    resp_execs = api_client.get(f"/api/v1/automations/{aut_id}/executions")
    assert resp_execs.status_code == 200
    assert len(resp_execs.json()) >= 1

    # 7. Pause and Resume Schedule
    resp_pause = api_client.post(f"/api/v1/scheduler/{sch_id}/pause")
    assert resp_pause.status_code == 200
    assert resp_pause.json()["status"] == "PAUSED"

    resp_resume = api_client.post(f"/api/v1/scheduler/{sch_id}/resume")
    assert resp_resume.status_code == 200
    assert resp_resume.json()["status"] == "SCHEDULED"


def test_deterministic_backend_simulation():
    """Test DeterministicSchedulerBackend clock advancement and execution."""
    container = get_scheduler_container()
    backend = container.deterministic_backend

    aut = Automation(
        automation_id="aut_sim",
        name="Simulated Job",
        definition=AutomationDefinition(
            steps=[AutomationStep(step_type=StepType.CREATE_TASK, configuration={"task_name": "Task"})]
        ),
    )
    container.automation_engine.create_automation(aut)

    start_time = backend.get_current_time()
    sch = Schedule(
        schedule_id="sch_sim",
        schedule_type=ScheduleType.INTERVAL,
        interval_seconds=300.0,
        next_run_at=start_time + timedelta(seconds=300),
        automation_id="aut_sim",
    )
    container.scheduler_service.create_schedule(sch)

    # Initially no due schedules
    execs_1 = backend.run_due()
    assert len(execs_1) == 0

    # Advance time by 5 minutes
    execs_2 = backend.advance_and_run(minutes=5)
    assert len(execs_2) == 1
    assert execs_2[0].status.value == "COMPLETED"


def test_event_driven_automation_integration():
    """Test external event triggering automations."""
    container = get_scheduler_container()
    backend = container.deterministic_backend

    aut = Automation(
        automation_id="aut_event",
        name="PR Review Automation",
        trigger={
            "trigger_type": "EVENT_TRIGGER",
            "definition": {"event_type": "github.pr.created"},
        },
        definition=AutomationDefinition(
            steps=[AutomationStep(step_type=StepType.SEND_NOTIFICATION, configuration={"title": "PR Opened"})]
        ),
    )
    container.automation_engine.create_automation(aut)

    event = ScheduleEvent(
        event_type="github.pr.created",
        source="github_webhook",
        payload={"pr_title": "Fix bug"},
    )

    execs = backend.emit_event(event)
    assert len(execs) == 1
    assert execs[0].status.value == "COMPLETED"
