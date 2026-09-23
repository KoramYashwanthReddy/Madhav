"""Plan Service for Plan CRUD, validation, revision, and historical versioning."""

import logging
from datetime import UTC, datetime

from max.reasoning.domain.enums import PlanStatus
from max.reasoning.domain.exceptions import OwnershipError, PlanNotFoundError
from max.reasoning.domain.plan import (
    Plan,
    PlanDependency,
    PlanDiff,
    PlanRisk,
    PlanStep,
    PlanValidationResult,
    PlanVersion,
)
from max.reasoning.domain.reasoning import ReasoningConstraint
from max.reasoning.repositories.plan_repository import InMemoryPlanRepository, PlanRepository
from max.reasoning.repositories.plan_version_repository import (
    InMemoryPlanVersionRepository,
    PlanVersionRepository,
)
from max.reasoning.services.comparison import PlanComparer
from max.reasoning.services.validator import PlanValidator

logger = logging.getLogger(__name__)


class PlanService:
    """Service managing plan lifecycle, revisions, version history, and validation."""

    def __init__(
        self,
        plan_repository: PlanRepository | None = None,
        version_repository: PlanVersionRepository | None = None,
        validator: PlanValidator | None = None,
        comparer: PlanComparer | None = None,
    ) -> None:
        self.plan_repository = plan_repository or InMemoryPlanRepository()
        self.version_repository = version_repository or InMemoryPlanVersionRepository()
        self.validator = validator or PlanValidator()
        self.comparer = comparer or PlanComparer()



    async def create_plan(
        self,
        owner_id: str,
        title: str,
        description: str,
        steps: list[PlanStep] | None = None,
        dependencies: list[PlanDependency] | None = None,
        risks: list[PlanRisk] | None = None,
        constraints: list[ReasoningConstraint] | None = None,
        metadata: dict[str, str | int | float | bool | list[str]] | None = None,
    ) -> Plan:
        """Create a new Plan and record Version 1 snapshot."""
        plan = Plan(
            owner_id=owner_id,
            title=title,
            description=description,
            version=1,
            status=PlanStatus.ACTIVE,
            steps=steps or [],
            dependencies=dependencies or [],
            risks=risks or [],
            constraints=constraints or [],
            metadata=metadata or {},
        )

        # Validate initial plan structure
        PlanValidator.assert_valid(plan)

        # Save plan record
        saved_plan = await self.plan_repository.save(plan)

        # Create Version 1 snapshot
        version_snapshot = PlanVersion(
            plan_id=saved_plan.plan_id,
            version_number=1,
            reason_for_change="Initial plan creation",
            snapshot=saved_plan.model_dump(),
        )
        await self.version_repository.save_version(version_snapshot)

        logger.info("Created Plan %s (v1) for owner %s", saved_plan.plan_id, owner_id)
        return saved_plan

    async def get_plan(self, plan_id: str, owner_id: str) -> Plan:
        """Retrieve plan by ID with owner validation."""
        plan = await self.plan_repository.get_by_id(plan_id)
        if not plan:
            raise PlanNotFoundError(plan_id)
        if plan.owner_id != owner_id:
            raise OwnershipError("Plan owner mismatch.")
        return plan

    async def list_plans(self, owner_id: str, skip: int = 0, limit: int = 50) -> list[Plan]:
        """List plans owned by owner_id."""
        return await self.plan_repository.list_plans(owner_id, skip=skip, limit=limit)

    async def validate_plan_id(self, plan_id: str, owner_id: str) -> PlanValidationResult:
        """Validate stored plan by ID."""
        plan = await self.get_plan(plan_id, owner_id)
        return PlanValidator.validate_plan(plan)

    async def revise_plan(
        self,
        plan_id: str,
        owner_id: str,
        reason_for_change: str,
        new_steps: list[PlanStep] | None = None,
        new_dependencies: list[PlanDependency] | None = None,
        new_risks: list[PlanRisk] | None = None,
        new_constraints: list[ReasoningConstraint] | None = None,
    ) -> Plan:
        """Revise an existing plan, creating a new PlanVersion snapshot."""
        plan = await self.get_plan(plan_id, owner_id)

        # Update fields if provided
        if new_steps is not None:
            plan.steps = new_steps
        if new_dependencies is not None:
            plan.dependencies = new_dependencies
        if new_risks is not None:
            plan.risks = new_risks
        if new_constraints is not None:
            plan.constraints = new_constraints

        # Validate revised plan structure
        PlanValidator.assert_valid(plan)

        prev_version = plan.version
        plan.version += 1
        plan.updated_at = datetime.now(UTC)

        # Save revised plan
        revised_plan = await self.plan_repository.save(plan)

        # Record new version snapshot
        version_snapshot = PlanVersion(
            plan_id=revised_plan.plan_id,
            version_number=revised_plan.version,
            reason_for_change=reason_for_change or f"Revised from v{prev_version}",
            previous_version_id=f"v{prev_version}",
            snapshot=revised_plan.model_dump(),
        )
        await self.version_repository.save_version(version_snapshot)

        logger.info(
            "Revised Plan %s to version %d for owner %s",
            revised_plan.plan_id,
            revised_plan.version,
            owner_id,
        )
        return revised_plan

    async def get_plan_versions(self, plan_id: str, owner_id: str) -> list[PlanVersion]:
        """List historical version snapshots for a plan."""
        await self.get_plan(plan_id, owner_id)  # Validate existence & ownership
        return await self.version_repository.list_versions(plan_id)

    async def compare_plan_versions(
        self, plan_id: str, owner_id: str, v1_number: int, v2_number: int
    ) -> PlanDiff:
        """Compare two historical version snapshots of a plan."""
        await self.get_plan(plan_id, owner_id)
        v1_snap = await self.version_repository.get_version(plan_id, v1_number)
        v2_snap = await self.version_repository.get_version(plan_id, v2_number)

        if not v1_snap:
            raise PlanNotFoundError(f"{plan_id}:v{v1_number}")
        if not v2_snap:
            raise PlanNotFoundError(f"{plan_id}:v{v2_number}")

        p1 = Plan.model_validate(v1_snap.snapshot)
        p2 = Plan.model_validate(v2_snap.snapshot)

        return PlanComparer.compare_plans(p1, p2)

    async def compare_versions(
        self, plan_id: str, owner_id: str, version_a: int, version_b: int
    ) -> PlanDiff:
        """Alias for compare_plan_versions."""
        return await self.compare_plan_versions(plan_id, owner_id, version_a, version_b)

