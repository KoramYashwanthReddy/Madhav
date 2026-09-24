"""Unit tests for Module 19 — Application Control."""

import pytest
from unittest.mock import MagicMock

from max.config.sections import ApplicationControlSettings
from max.application_control import (
    ApplicationControlContainer,
    ApplicationControlService,
    get_application_control_container,
    reset_application_control_container,
)
from max.application_control.backends.mock import MockApplicationControlBackend
from max.application_control.domain.enums import (
    ApplicationActionFailureReason,
    ApplicationActionStatus,
    ApplicationActionType,
    ApplicationAuditEventType,
    ApplicationCategory,
    ApplicationState,
    ApplicationStatus,
    ApplicationType,
)
from max.application_control.domain.exceptions import (
    ApplicationBlockedError,
    ApplicationControlError,
    ApplicationElevationDeniedError,
    ApplicationInstanceLimitExceededError,
    ApplicationNotFoundError,
    ApplicationPolicyViolationError,
    ApplicationProcessNotFoundError,
)
from max.application_control.domain.models import (
    Application,
    ApplicationActionRequest,
    ApplicationActionResult,
    ApplicationAuditEvent,
    ApplicationInstance,
    ApplicationPolicy,
    ApplicationWindow,
)
from max.application_control.repositories import (
    ApplicationAuditRepository,
    ApplicationInstanceRepository,
    ApplicationPolicyRepository,
    ApplicationRepository,
)
from max.application_control.security.app_policy import ApplicationPolicyService
from max.application_control.services.tool_integration import register_application_tools
from max.tools.services.registry import ToolRegistryService


# ---------------------------------------------------------------------------
# Domain Models & Enums Tests
# ---------------------------------------------------------------------------


def test_application_model_creation():
    app = Application(
        app_id="calc",
        display_name="Calculator",
        executable="calc.exe",
        category=ApplicationCategory.UTILITY,
    )
    assert app.app_id == "calc"
    assert app.display_name == "Calculator"
    assert app.executable == "calc.exe"
    assert app.category == ApplicationCategory.UTILITY
    assert app.is_installed is True


def test_application_instance_model():
    inst = ApplicationInstance(
        app_id="notepad",
        pid=1234,
        status=ApplicationStatus.RUNNING,
    )
    assert inst.app_id == "notepad"
    assert inst.pid == 1234
    assert inst.is_active is True


# ---------------------------------------------------------------------------
# Backend Tests (Mock Backend)
# ---------------------------------------------------------------------------


def test_mock_backend_discovery():
    backend = MockApplicationControlBackend()
    apps = backend.discover_applications()
    assert len(apps) > 0
    app_ids = [a.app_id for a in apps]
    assert "notepad" in app_ids
    assert "calculator" in app_ids


def test_mock_backend_launch_and_close():
    backend = MockApplicationControlBackend()
    apps = backend.discover_applications()
    notepad = next(a for a in apps if a.app_id == "notepad")

    req = ApplicationActionRequest(
        action_type=ApplicationActionType.LAUNCH,
        app_id=notepad.app_id,
    )
    res = backend.launch_application(notepad, req)
    assert res.is_success
    assert res.instance is not None
    assert res.instance.pid > 0

    running = backend.get_running_instances()
    assert len(running) == 1

    # Focus
    focus_req = ApplicationActionRequest(
        action_type=ApplicationActionType.FOCUS,
        app_id=notepad.app_id,
        instance_id=res.instance.instance_id,
    )
    focus_res = backend.focus_application(res.instance, focus_req)
    assert focus_res.is_success

    # Close
    close_req = ApplicationActionRequest(
        action_type=ApplicationActionType.CLOSE,
        app_id=notepad.app_id,
        instance_id=res.instance.instance_id,
    )
    close_res = backend.close_application(res.instance, close_req)
    assert close_res.is_success

    running_after = backend.get_running_instances()
    assert len(running_after) == 0


def test_mock_backend_failure_injection():
    backend = MockApplicationControlBackend()
    backend.should_fail_launch = True
    apps = backend.discover_applications()
    calc = next(a for a in apps if a.app_id == "calculator")

    req = ApplicationActionRequest(
        action_type=ApplicationActionType.LAUNCH,
        app_id=calc.app_id,
    )
    res = backend.launch_application(calc, req)
    assert not res.is_success
    assert res.failure_reason == ApplicationActionFailureReason.EXECUTION_FAILED


# ---------------------------------------------------------------------------
# Repository Tests
# ---------------------------------------------------------------------------


def test_application_repository():
    repo = ApplicationRepository()
    app1 = Application(app_id="app1", display_name="Test App One", executable="app1.exe")
    app2 = Application(app_id="app2", display_name="Test App Two", executable="app2.exe")

    repo.save(app1)
    repo.save(app2)

    assert repo.count() == 2
    assert repo.get("app1") == app1
    assert repo.get_by_name_or_executable("app2.exe") == app2
    assert repo.get_by_name_or_executable("Test App One") == app1
    assert repo.get_by_name_or_executable("nonexistent") is None


def test_instance_repository():
    repo = ApplicationInstanceRepository()
    inst = ApplicationInstance(app_id="app1", pid=100)
    repo.save(inst)

    assert repo.get(inst.instance_id) == inst
    assert repo.get_by_pid(100) == inst
    assert repo.count_active_for_app("app1") == 1

    inst_closed = inst.model_copy(update={"state": ApplicationState.CLOSED})
    repo.save(inst_closed)
    assert repo.count_active_for_app("app1") == 0


def test_audit_repository():
    repo = ApplicationAuditRepository()
    evt = ApplicationAuditEvent(
        event_type=ApplicationAuditEventType.LAUNCHED,
        app_id="app1",
    )
    repo.record(evt)
    assert repo.count() == 1
    assert repo.list_events(app_id="app1")[0].event_type == ApplicationAuditEventType.LAUNCHED


# ---------------------------------------------------------------------------
# Policy & Security Tests
# ---------------------------------------------------------------------------


def test_policy_blocked_executable():
    settings = ApplicationControlSettings(blocked_executables=["malware.exe"])
    service = ApplicationPolicyService(settings=settings)
    app = Application(app_id="bad", display_name="Bad App", executable="malware.exe")

    with pytest.raises(ApplicationBlockedError):
        service.validate_launch(app)


def test_policy_allowed_executables_whitelist():
    settings = ApplicationControlSettings(allowed_executables=["notepad.exe"])
    service = ApplicationPolicyService(settings=settings)
    app1 = Application(app_id="n", display_name="Notepad", executable="notepad.exe")
    app2 = Application(app_id="c", display_name="Calc", executable="calc.exe")

    service.validate_launch(app1)  # should pass

    with pytest.raises(ApplicationBlockedError):
        service.validate_launch(app2)


def test_policy_max_instances():
    settings = ApplicationControlSettings(max_instances_per_app=1)
    inst_repo = ApplicationInstanceRepository()
    inst_repo.save(ApplicationInstance(app_id="app1", pid=500))

    service = ApplicationPolicyService(settings=settings, instance_repo=inst_repo)
    app = Application(app_id="app1", display_name="App 1", executable="app1.exe")

    with pytest.raises(ApplicationInstanceLimitExceededError):
        service.validate_launch(app)


# ---------------------------------------------------------------------------
# Service Facade Tests
# ---------------------------------------------------------------------------


def test_application_control_service_lifecycle():
    backend = MockApplicationControlBackend()
    service = ApplicationControlService(backend=backend)

    # List apps
    apps = service.list_applications()
    assert len(apps) > 0

    # Launch notepad
    launch_res = service.launch_application("notepad")
    assert launch_res.is_success
    assert launch_res.instance is not None

    # Status check
    status = service.get_application_status("notepad")
    assert status["active_instances_count"] == 1

    # Windows
    windows = service.get_application_windows("notepad")
    assert len(windows) > 0

    # Focus
    focus_res = service.focus_application("notepad")
    assert focus_res.is_success

    # Close
    close_res = service.close_application("notepad")
    assert close_res.is_success

    # Audit events
    events = service.get_audit_events(app_id="notepad")
    assert len(events) >= 2


def test_application_control_service_restart():
    backend = MockApplicationControlBackend()
    service = ApplicationControlService(backend=backend)

    service.launch_application("calculator")
    restart_res = service.restart_application("calculator")
    assert restart_res.is_success
    assert restart_res.instance is not None


# ---------------------------------------------------------------------------
# Tool Integration & Container Tests
# ---------------------------------------------------------------------------


def test_tool_registration():
    registry = ToolRegistryService()
    tool_ids = register_application_tools(registry)
    assert len(tool_ids) == 7

    tools, _ = registry.list_tools()
    tool_names = [t.name for t in tools]
    assert "app.list" in tool_names
    assert "app.launch" in tool_names
    assert "app.close" in tool_names


def test_container_lifecycle():
    reset_application_control_container()
    container = get_application_control_container(use_mock_backend=True)
    assert isinstance(container, ApplicationControlContainer)
    assert isinstance(container.backend, MockApplicationControlBackend)
    assert container.application_control_service is not None

    reset_application_control_container()
