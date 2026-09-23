"""Plan Comparer service for computing diffs between plan versions."""

from max.reasoning.domain.plan import Plan, PlanDiff


class PlanComparer:
    """Computes structured diff comparison between two plan versions."""

    @staticmethod
    def compare_plans(plan1: Plan, plan2: Plan) -> PlanDiff:
        """Compare plan1 (old) and plan2 (new) and return PlanDiff."""
        steps1_map = {s.step_id: s for s in plan1.steps}
        steps2_map = {s.step_id: s for s in plan2.steps}

        added_steps: list[str] = []
        removed_steps: list[str] = []
        changed_steps: list[str] = []

        # Find added and changed steps
        for step_id, s2 in steps2_map.items():
            if step_id not in steps1_map:
                # Try matching by title if step_id changed
                matched_old = False
                for old_id, s1 in steps1_map.items():
                    if s1.title == s2.title and old_id not in steps2_map:
                        matched_old = True
                        if s1.description != s2.description or s1.status != s2.status:
                            changed_steps.append(f"Step '{s2.title}' (modified)")
                        break
                if not matched_old:
                    added_steps.append(f"Step '{s2.title}' (id: {step_id})")
            else:
                s1 = steps1_map[step_id]
                if (
                    s1.title != s2.title
                    or s1.description != s2.description
                    or s1.status != s2.status
                    or s1.sequence != s2.sequence
                ):
                    changed_steps.append(f"Step '{s2.title}' (modified)")

        # Find removed steps
        for step_id, s1 in steps1_map.items():
            if step_id not in steps2_map:
                if not any(s2.title == s1.title for s2 in plan2.steps):
                    removed_steps.append(f"Step '{s1.title}' (id: {step_id})")

        # Compare dependencies
        deps1_set = {f"{d.source_step_id}->{d.target_step_id}" for d in plan1.dependencies}
        deps2_set = {f"{d.source_step_id}->{d.target_step_id}" for d in plan2.dependencies}
        changed_deps = [
            f"Added dependency {d}" for d in (deps2_set - deps1_set)
        ] + [f"Removed dependency {d}" for d in (deps1_set - deps2_set)]

        # Compare constraints
        c1_set = {f"{c.type}:{c.description}" for c in plan1.constraints}
        c2_set = {f"{c.type}:{c.description}" for c in plan2.constraints}
        changed_cst = [
            f"Added constraint {c}" for c in (c2_set - c1_set)
        ] + [f"Removed constraint {c}" for c in (c1_set - c2_set)]

        # Compare risks
        r1_set = {r.description for r in plan1.risks}
        r2_set = {r.description for r in plan2.risks}
        changed_rsk = [
            f"Added risk: {r}" for r in (r2_set - r1_set)
        ] + [f"Removed risk: {r}" for r in (r1_set - r2_set)]

        return PlanDiff(
            added_steps=added_steps,
            removed_steps=removed_steps,
            changed_steps=changed_steps,
            changed_dependencies=changed_deps,
            changed_constraints=changed_cst,
            changed_risks=changed_rsk,
        )
