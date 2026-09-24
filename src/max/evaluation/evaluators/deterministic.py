"""Deterministic evaluator implementation for Module 32."""

from typing import Any

from max.evaluation.domain.enums import EvaluationDimension, EvaluatorType, ScoreScale
from max.evaluation.domain.models import EvaluationCase, EvaluationScore, EvaluationTarget
from max.evaluation.evaluators.base import EvaluationProvider


class DeterministicEvaluator(EvaluationProvider):
    """Evaluates cases deterministically without AI model inference."""

    @property
    def name(self) -> str:
        return "DeterministicEvaluator"

    async def evaluate_case(
        self,
        case: EvaluationCase,
        target: EvaluationTarget,
        actual_output: str,
        execution_context: dict[str, Any] | None = None,
    ) -> list[EvaluationScore]:
        ctx = execution_context or {}
        scores: list[EvaluationScore] = []

        # 1. Exact or expected output check
        if case.expected_output is not None:
            expected = case.expected_output.strip().lower()
            actual = actual_output.strip().lower()
            match_pass = expected in actual or actual in expected
            scores.append(
                EvaluationScore(
                    value=1.0 if match_pass else 0.0,
                    scale=ScoreScale.ZERO_TO_ONE,
                    metric_name="exact_match_score",
                    dimension=EvaluationDimension.CORRECTNESS,
                    confidence=1.0,
                    evaluator_name=self.name,
                    evaluator_type=EvaluatorType.DETERMINISTIC,
                    reasoning_summary=(
                        f"Expected content '{case.expected_output}' found in output."
                        if match_pass
                        else f"Expected content '{case.expected_output}' missing from output."
                    ),
                )
            )

        # 2. Tool Selection & Argument Accuracy Check
        if case.expected_tools:
            used_tools = ctx.get("used_tools", [])
            tools_pass = all(tool in used_tools for tool in case.expected_tools)
            scores.append(
                EvaluationScore(
                    value=1.0 if tools_pass else 0.0,
                    scale=ScoreScale.ZERO_TO_ONE,
                    metric_name="tool_selection_score",
                    dimension=EvaluationDimension.TOOL_SELECTION,
                    confidence=1.0,
                    evaluator_name=self.name,
                    evaluator_type=EvaluatorType.DETERMINISTIC,
                    reasoning_summary=(
                        f"All expected tools {case.expected_tools} were selected."
                        if tools_pass
                        else f"Tool selection mismatch. Expected: {case.expected_tools}, Used: {used_tools}."
                    ),
                )
            )

        # 3. Security & Permission Compliance Check
        if case.expected_security_action:
            sec_action = ctx.get("security_action", "")
            sec_pass = case.expected_security_action.lower() in sec_action.lower() or case.expected_security_action.lower() in actual_output.lower()
            scores.append(
                EvaluationScore(
                    value=1.0 if sec_pass else 0.0,
                    scale=ScoreScale.ZERO_TO_ONE,
                    metric_name="security_compliance_score",
                    dimension=EvaluationDimension.SECURITY,
                    confidence=1.0,
                    evaluator_name=self.name,
                    evaluator_type=EvaluatorType.DETERMINISTIC,
                    reasoning_summary=(
                        f"Security enforcement matched expected action '{case.expected_security_action}'."
                        if sec_pass
                        else f"Security violation or mismatch. Expected '{case.expected_security_action}'."
                    ),
                )
            )

        # 4. Latency Threshold Check
        latency_ms = float(ctx.get("latency_ms", 0.0))
        max_latency = float(case.constraints.get("max_latency_ms", 30000.0))
        lat_pass = latency_ms <= max_latency
        scores.append(
            EvaluationScore(
                value=1.0 if lat_pass else 0.0,
                scale=ScoreScale.ZERO_TO_ONE,
                metric_name="latency_compliance_score",
                dimension=EvaluationDimension.LATENCY,
                confidence=1.0,
                evaluator_name=self.name,
                evaluator_type=EvaluatorType.DETERMINISTIC,
                reasoning_summary=f"Latency {latency_ms:.1f}ms within max limit {max_latency}ms.",
            )
        )

        # Fallback general correctness score if no specific rules triggered
        if not scores:
            scores.append(
                EvaluationScore(
                    value=1.0 if actual_output else 0.0,
                    scale=ScoreScale.ZERO_TO_ONE,
                    metric_name="output_presence_score",
                    dimension=EvaluationDimension.CORRECTNESS,
                    confidence=1.0,
                    evaluator_name=self.name,
                    evaluator_type=EvaluatorType.DETERMINISTIC,
                    reasoning_summary="Output present and non-empty.",
                )
            )

        return scores
