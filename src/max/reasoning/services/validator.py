"""Plan Validator service with circular dependency detection."""

from max.reasoning.domain.enums import CompletenessStatus, ConstraintClassification
from max.reasoning.domain.exceptions import CircularDependencyError, PlanValidationError
from max.reasoning.domain.plan import Plan, PlanValidationResult


class PlanValidator:
    """Deterministic validator for Plan integrity, dependencies, constraints, and completeness."""

    @classmethod
    def validate_plan(cls, plan: Plan) -> PlanValidationResult:
        """Perform comprehensive deterministic validation on a Plan."""
        errors: list[str] = []
        warnings: list[str] = []
        has_cycles = False

        if not plan.steps:
            errors.append("Plan contains no steps.")
            return PlanValidationResult(
                is_valid=False,
                status=CompletenessStatus.INVALID,
                errors=errors,
                warnings=warnings,
                has_circular_dependencies=False,
            )

        # 1. Check duplicate step_ids
        step_map = {}
        for step in plan.steps:
            if step.step_id in step_map:
                errors.append(f"Duplicate step_id detected: '{step.step_id}'.")
            else:
                step_map[step.step_id] = step

        # 2. Validate dependencies reference valid existing steps
        adjacency: dict[str, list[str]] = {s.step_id: [] for s in plan.steps}
        for step in plan.steps:
            for dep_id in step.dependencies:
                if dep_id not in step_map:
                    errors.append(
                        f"Step '{step.step_id}' references unknown dependency step_id '{dep_id}'."
                    )
                else:
                    if step.step_id not in adjacency[dep_id]:
                        adjacency[dep_id].append(step.step_id)


        # Also validate explicit dependencies list
        for dep in plan.dependencies:
            if dep.source_step_id not in step_map:
                errors.append(
                    f"PlanDependency source_step_id '{dep.source_step_id}' missing in steps."
                )
            if dep.target_step_id not in step_map:
                errors.append(
                    f"PlanDependency target_step_id '{dep.target_step_id}' missing in steps."
                )
            if (
                dep.source_step_id in adjacency
                and dep.target_step_id not in adjacency[dep.source_step_id]
            ):
                adjacency[dep.source_step_id].append(dep.target_step_id)

        # 3. Detect circular dependencies (DFS Cycle Detection)
        cycle = cls._detect_cycle(adjacency)
        if cycle:
            has_cycles = True
            errors.append(f"Circular dependency detected: {' -> '.join(cycle)}.")

        # 4. Validate hard constraints
        for constraint in plan.constraints:
            if constraint.classification == ConstraintClassification.HARD:
                if constraint.type.lower() == "max_steps":
                    try:
                        limit = int(constraint.description)
                        cnt = len(plan.steps)
                        if cnt > limit:
                            msg = f"Hard constraint violation: {cnt} steps exceeds {limit}."
                            errors.append(msg)



                    except ValueError:
                        pass


        # 5. Determine overall completeness status
        if errors:
            status = CompletenessStatus.INVALID
        elif any(s.status.name == "BLOCKED" for s in plan.steps):
            status = CompletenessStatus.BLOCKED
        elif any(s.status.name in ("PENDING", "IN_PROGRESS", "READY") for s in plan.steps):
            status = CompletenessStatus.PARTIAL
        else:
            status = CompletenessStatus.COMPLETE

        is_valid = len(errors) == 0

        return PlanValidationResult(
            is_valid=is_valid,
            status=status,
            errors=errors,
            warnings=warnings,
            has_circular_dependencies=has_cycles,
        )

    def validate(self, plan: Plan) -> PlanValidationResult:
        """Instance method alias for validate_plan."""
        return self.validate_plan(plan)

    def validate_or_raise(self, plan: Plan) -> None:
        """Instance method alias for assert_valid."""
        self.assert_valid(plan)

    @classmethod
    def assert_valid(cls, plan: Plan) -> None:
        """Validate plan and raise PlanValidationError / CircularDependencyError if invalid."""
        res = cls.validate_plan(plan)
        if res.has_circular_dependencies:
            # Re-run cycle detection to extract exact cycle loop
            adjacency = {s.step_id: list(s.dependencies) for s in plan.steps}
            cycle = cls._detect_cycle(adjacency) or ["unknown_cycle"]
            raise CircularDependencyError(cycle=cycle)
        if not res.is_valid:
            raise PlanValidationError(
                f"Plan validation failed: {'; '.join(res.errors)}",
                details={"errors": res.errors, "warnings": res.warnings},
            )


    @staticmethod
    def _detect_cycle(adjacency: dict[str, list[str]]) -> list[str] | None:
        """Detect cycles in directed graph using DFS recursion stack."""
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str) -> list[str] | None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    res = dfs(neighbor)
                    if res:
                        return res
                elif neighbor in rec_stack:
                    # Cycle found! Extract cycle path loop
                    cycle_start_idx = path.index(neighbor)
                    return path[cycle_start_idx:] + [neighbor]

            path.pop()
            rec_stack.remove(node)
            return None

        for node in adjacency:
            if node not in visited:
                cycle_found = dfs(node)
                if cycle_found:
                    return cycle_found

        return None
