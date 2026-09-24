"""ResearchPlanner service for Module 21 — Web Intelligence."""

from max.web_intelligence.domain.enums import ResearchMode
from max.web_intelligence.domain.models import (
    ResearchPlan,
    ResearchPlanStep,
    ResearchRequest,
)


class ResearchPlanner:
    """Formulates structured multi-step research execution plans."""

    def create_plan(self, request: ResearchRequest) -> ResearchPlan:
        """Generate a step-by-step ResearchPlan based on mode, objective, and constraints."""
        steps: list[ResearchPlanStep] = []
        planned_queries: list[str] = []

        step_num = 1
        steps.append(
            ResearchPlanStep(
                step_number=step_num,
                action_type="PLANNING",
                description=f"Formulated research plan for topic '{request.objective.topic}' in {request.mode.value} mode.",
                completed=True,
            )
        )
        step_num += 1

        steps.append(
            ResearchPlanStep(
                step_number=step_num,
                action_type="QUERY_GENERATION",
                description="Generate complementary search queries.",
            )
        )
        step_num += 1

        steps.append(
            ResearchPlanStep(
                step_number=step_num,
                action_type="SEARCH",
                description="Execute queries against search provider to discover candidate sources.",
            )
        )
        step_num += 1

        steps.append(
            ResearchPlanStep(
                step_number=step_num,
                action_type="COLLECTION",
                description="Acquire structured page content for candidate sources.",
            )
        )
        step_num += 1

        steps.append(
            ResearchPlanStep(
                step_number=step_num,
                action_type="EXTRACTION",
                description="Extract factual claims, quotes, and structured evidence.",
            )
        )
        step_num += 1

        if request.mode in (ResearchMode.DEEP_RESEARCH, ResearchMode.SOURCE_COMPARISON, ResearchMode.FACT_CHECK):
            steps.append(
                ResearchPlanStep(
                    step_number=step_num,
                    action_type="COMPARISON",
                    description="Perform cross-source evidence comparison and conflict detection.",
                )
            )
            step_num += 1

        steps.append(
            ResearchPlanStep(
                step_number=step_num,
                action_type="SYNTHESIS",
                description="Synthesize findings, generate citations, and compile quality report.",
            )
        )

        # Generate initial query ideas
        planned_queries.append(request.objective.question)
        planned_queries.append(f"{request.objective.topic} latest developments")
        if request.objective.sub_questions:
            for subq in request.objective.sub_questions[:2]:
                planned_queries.append(subq)

        return ResearchPlan(
            research_id=request.id,
            steps=steps,
            planned_queries=planned_queries,
        )
