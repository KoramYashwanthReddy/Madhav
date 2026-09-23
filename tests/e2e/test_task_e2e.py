"""End-to-End tests for Module 12 Task Engine."""

from max.reasoning.domain.enums import CompletenessStatus, PlanStatus
from max.reasoning.domain.plan import Plan, PlanDependency, PlanStep
from max.tasks.domain.enums import TaskReadinessStatus, TaskStatus
from max.tasks.services.task_service import TaskService


def test_e2e_plan_to_task_workflow() -> None:
    """Full E2E test verifying plan conversion -> dependency resolution -> lifecycle transitions -> audit trail."""
    service = TaskService()

    # Step 1: Create Module 11 Reasoning Plan
    plan = Plan(
        plan_id="e2e_plan_001",
        title="E2E Deployment Plan",
        description="Plan for end to end testing",
        reasoning_id="e2e_reas_001",
        owner_id="e2e_user",
        version=1,
        steps=[
            PlanStep(
                sequence=1,
                step_id="step_prep",
                title="Prepare Environment",
                description="Setup configuration",
            ),
            PlanStep(
                sequence=2,
                step_id="step_build",
                title="Build Application",
                description="Compile and package",
                dependencies=["step_prep"],
            ),
            PlanStep(
                sequence=3,
                step_id="step_deploy",
                title="Deploy Package",
                description="Push to server",
                dependencies=["step_build"],
            ),
        ],
        dependencies=[
            PlanDependency(source_step_id="step_prep", target_step_id="step_build"),
            PlanDependency(source_step_id="step_build", target_step_id="step_deploy"),
        ],
        status=PlanStatus.ACTIVE,
        completeness=CompletenessStatus.COMPLETE,
    )

    # Step 2: Convert Plan into Tasks
    tasks, deps = service.generate_tasks_from_plan(plan)
    assert len(tasks) == 3
    assert len(deps) >= 2

    task_prep = next(t for t in tasks if t.plan_step_id == "step_prep")
    task_build = next(t for t in tasks if t.plan_step_id == "step_build")
    task_deploy = next(t for t in tasks if t.plan_step_id == "step_deploy")

    # Step 3: Verify initial readiness states
    assert service.calculate_readiness(task_prep.id) == TaskReadinessStatus.READY
    assert service.calculate_readiness(task_build.id) == TaskReadinessStatus.BLOCKED
    assert service.calculate_readiness(task_deploy.id) == TaskReadinessStatus.BLOCKED

    # Step 4: Progress prep task to completion
    service.start_task(task_prep.id)
    service.complete_task(task_prep.id)

    # Step 5: Verify build task automatically unlocked to READY
    assert service.calculate_readiness(task_build.id) == TaskReadinessStatus.READY
    assert service.get_task(task_build.id).status == TaskStatus.READY

    # Step 6: Progress build task to completion
    service.start_task(task_build.id)
    service.complete_task(task_build.id)

    # Step 7: Verify deploy task unlocked
    assert service.calculate_readiness(task_deploy.id) == TaskReadinessStatus.READY
    assert service.get_task(task_deploy.id).status == TaskStatus.READY

    # Step 8: Progress deploy task to completion
    service.start_task(task_deploy.id)
    service.complete_task(task_deploy.id)

    # Step 9: Check task history audit trail for deploy task
    history_entries, total_entries = service.get_task_history(task_deploy.id)
    assert total_entries >= 3
    statuses = [e.new_status for e in history_entries]
    assert TaskStatus.COMPLETED in statuses
    assert TaskStatus.IN_PROGRESS in statuses
