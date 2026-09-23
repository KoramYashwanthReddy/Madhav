"""Plan-to-Task mapper and task generation service."""


from max.reasoning.domain.plan import Plan, PlanStep
from max.tasks.domain.dependency import TaskDependency
from max.tasks.domain.enums import (
    DependencyType,
    TaskPriority,
    TaskReferenceType,
    TaskSource,
    TaskStatus,
    TaskType,
)
from max.tasks.domain.references import TaskReference
from max.tasks.domain.task import Task


class PlanTaskMapper:
    """Maps Module 11 Reasoning Plans into Module 12 Tasks."""

    @staticmethod
    def map_plan_to_tasks(
        plan: Plan,
        owner_id: str | None = None,
        existing_tasks: list[Task] | None = None,
    ) -> tuple[list[Task], list[TaskDependency]]:
        """Convert a Plan and its steps into Task entities and TaskDependencies.

        Implements idempotency: If a task already exists for (plan_id, plan_version, step_id),
        the existing task is preserved and not duplicated.
        """
        effective_owner_id = owner_id or plan.owner_id
        existing_by_step_id: dict[str, Task] = {}

        if existing_tasks:
            for task in existing_tasks:
                if task.plan_id == plan.plan_id and task.plan_version == plan.version and task.plan_step_id:
                    existing_by_step_id[task.plan_step_id] = task

        generated_tasks: list[Task] = []
        step_id_to_task_id: dict[str, str] = {}

        for step in plan.steps:
            if step.step_id in existing_by_step_id:
                task = existing_by_step_id[step.step_id]
            else:
                task = PlanTaskMapper._map_step_to_task(step=step, plan=plan, owner_id=effective_owner_id)

            generated_tasks.append(task)
            step_id_to_task_id[step.step_id] = task.id

        # Generate dependencies based on step.dependencies and plan.dependencies
        dependencies: list[TaskDependency] = []
        seen_dep_keys: set[tuple[str, str]] = set()

        for step in plan.steps:
            target_task_id = step_id_to_task_id[step.step_id]
            for source_step_id in step.dependencies:
                if source_step_id in step_id_to_task_id:
                    source_task_id = step_id_to_task_id[source_step_id]
                    key = (source_task_id, target_task_id)
                    if key not in seen_dep_keys and source_task_id != target_task_id:
                        seen_dep_keys.add(key)
                        dependencies.append(
                            TaskDependency(
                                source_task_id=target_task_id,
                                target_task_id=source_task_id,
                                dependency_type=DependencyType.DEPENDS_ON,
                            )
                        )

        # Also map explicit plan.dependencies list
        for plan_dep in plan.dependencies:
            src_step = plan_dep.source_step_id
            tgt_step = plan_dep.target_step_id
            if src_step in step_id_to_task_id and tgt_step in step_id_to_task_id:
                source_task_id = step_id_to_task_id[src_step]
                target_task_id = step_id_to_task_id[tgt_step]
                key = (source_task_id, target_task_id)
                if key not in seen_dep_keys and source_task_id != target_task_id:
                    seen_dep_keys.add(key)
                    dependencies.append(
                        TaskDependency(
                            source_task_id=target_task_id,
                            target_task_id=source_task_id,
                            dependency_type=DependencyType.DEPENDS_ON,
                        )
                    )

        return generated_tasks, dependencies

    @staticmethod
    def _map_step_to_task(step: PlanStep, plan: Plan, owner_id: str) -> Task:
        """Map a single PlanStep to a Task domain entity."""
        references = [
            TaskReference(
                reference_type=TaskReferenceType.PLAN,
                reference_id=plan.plan_id,
                summary=f"Plan version {plan.version}",
                metadata={"plan_version": plan.version},
            ),
            TaskReference(
                reference_type=TaskReferenceType.PLAN_STEP,
                reference_id=step.step_id,
                summary=f"Step {step.sequence}: {step.title}",
                metadata={"sequence": step.sequence},
            ),
        ]
        reasoning_id = getattr(plan, "reasoning_id", None) or plan.metadata.get("reasoning_id")
        if reasoning_id:
            references.append(
                TaskReference(
                    reference_type=TaskReferenceType.REASONING,
                    reference_id=str(reasoning_id),
                    summary="Origin reasoning request",
                )
            )


        task_type = TaskType.PLANNING
        if "research" in step.title.lower() or "read" in step.title.lower():
            task_type = TaskType.RESEARCH
        elif "code" in step.title.lower() or "implement" in step.title.lower():
            task_type = TaskType.CODING
        elif "review" in step.title.lower() or "test" in step.title.lower():
            task_type = TaskType.REVIEW
        elif "analyze" in step.title.lower():
            task_type = TaskType.ANALYSIS

        return Task(
            owner_id=owner_id,
            title=step.title,
            description=step.description,
            type=task_type,
            status=TaskStatus.PENDING,
            priority=TaskPriority.NORMAL,
            progress=0,
            source=TaskSource.PLAN,
            plan_id=plan.plan_id,
            plan_version=plan.version,
            plan_step_id=step.step_id,
            reasoning_id=str(reasoning_id) if reasoning_id else None,
            references=references,

            metadata={
                "sequence": step.sequence,
                "estimated_complexity": step.estimated_complexity.value,
                "risk_level": step.risk_level.value,
                "expected_output": step.expected_output,
                "prerequisites": step.prerequisites,
            },
        )
