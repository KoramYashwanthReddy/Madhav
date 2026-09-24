"""Reference-based evaluator implementation for Module 32."""

from typing import Any

from max.evaluation.domain.enums import EvaluationDimension, EvaluatorType, ScoreScale
from max.evaluation.domain.models import EvaluationCase, EvaluationScore, EvaluationTarget
from max.evaluation.evaluators.base import EvaluationProvider


class ReferenceBasedEvaluator(EvaluationProvider):
    """Evaluates output against reference ground truth facts and citations."""

    @property
    def name(self) -> str:
        return "ReferenceBasedEvaluator"

    async def evaluate_case(
        self,
        case: EvaluationCase,
        target: EvaluationTarget,
        actual_output: str,
        execution_context: dict[str, Any] | None = None,
    ) -> list[EvaluationScore]:
        scores: list[EvaluationScore] = []
        actual_lower = actual_output.lower()

        # 1. Reference Facts Groundedness & Coverage
        if case.reference_facts:
            matched_facts = 0
            for fact in case.reference_facts:
                if fact.lower() in actual_lower:
                    matched_facts += 1
            fact_score = matched_facts / len(case.reference_facts)
            scores.append(
                EvaluationScore(
                    value=round(fact_score, 4),
                    scale=ScoreScale.ZERO_TO_ONE,
                    metric_name="fact_coverage_score",
                    dimension=EvaluationDimension.FACTUALITY,
                    confidence=0.9,
                    evaluator_name=self.name,
                    evaluator_type=EvaluatorType.REFERENCE_BASED,
                    reasoning_summary=f"Matched {matched_facts}/{len(case.reference_facts)} reference facts.",
                )
            )

        # 2. Reference Citations Presence
        expected_citations = case.constraints.get("expected_citations", [])
        if expected_citations:
            matched_cites = 0
            for cite in expected_citations:
                if str(cite).lower() in actual_lower:
                    matched_cites += 1
            cite_score = matched_cites / len(expected_citations)
            scores.append(
                EvaluationScore(
                    value=round(cite_score, 4),
                    scale=ScoreScale.ZERO_TO_ONE,
                    metric_name="citation_precision",
                    dimension=EvaluationDimension.CITATION_QUALITY,
                    confidence=0.9,
                    evaluator_name=self.name,
                    evaluator_type=EvaluatorType.REFERENCE_BASED,
                    reasoning_summary=f"Found {matched_cites}/{len(expected_citations)} expected citations.",
                )
            )

        if not scores:
            scores.append(
                EvaluationScore(
                    value=1.0,
                    scale=ScoreScale.ZERO_TO_ONE,
                    metric_name="reference_check_passed",
                    dimension=EvaluationDimension.CORRECTNESS,
                    confidence=1.0,
                    evaluator_name=self.name,
                    evaluator_type=EvaluatorType.REFERENCE_BASED,
                    reasoning_summary="No specific reference constraints violated.",
                )
            )

        return scores
