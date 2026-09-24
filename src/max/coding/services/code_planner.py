"""CodePlanner service for formulating structured implementation plans."""

from max.coding.domain.enums import CodingMode
from max.coding.domain.exceptions import InvalidCodingPlanError
from max.coding.domain.models import CodePlan, CodePlanStep, CodingRequest


class CodePlanner:
    """Formulates multi-step implementation plans for software engineering tasks."""

    def create_plan(self, request: CodingRequest) -> CodePlan:
        """Generate a structured CodePlan based on coding mode and task objective."""
        steps: list[CodePlanStep] = []
        step_num = 1

        steps.append(
            CodePlanStep(
                step_number=step_num,
                action_type="INSPECT",
                description=f"Inspect repository structure and target files for '{request.objective.summary}'.",
                target_files=request.objective.target_files,
                completed=True,
            )
        )
        step_num += 1

        if request.mode in (CodingMode.BUG_FIX, CodingMode.FEATURE_IMPLEMENTATION, CodingMode.REFACTOR):
            steps.append(
                CodePlanStep(
                    step_number=step_num,
                    action_type="EDIT",
                    description="Generate targeted patches for affected source files.",
                    target_files=request.objective.target_files,
                )
            )
            step_num += 1

            steps.append(
                CodePlanStep(
                    step_number=step_num,
                    action_type="VALIDATE",
                    description="Run automated validation pipeline (tests, build, linters, typecheckers).",
                )
            )
            step_num += 1

        elif request.mode == CodingMode.TEST_GENERATION:
            steps.append(
                CodePlanStep(
                    step_number=step_num,
                    action_type="CREATE_TEST",
                    description="Create new test cases matching existing test framework conventions.",
                    target_files=request.objective.target_files,
                )
            )
            step_num += 1

        steps.append(
            CodePlanStep(
                step_number=step_num,
                action_type="REVIEW",
                description="Perform final code review and summarize changes.",
            )
        )

        return CodePlan(
            session_id=request.id,
            objective=request.objective.summary,
            steps=steps,
            affected_files=request.objective.target_files,
        )

    def validate_plan(self, plan: CodePlan) -> None:
        """Verify plan contains valid steps and non-empty target objectives."""
        if not plan.steps:
            raise InvalidCodingPlanError("Code plan contains no operational steps.")
        if not plan.objective:
            raise InvalidCodingPlanError("Code plan objective cannot be empty.")
