"""Coverage tracking service for Module 32."""

from max.evaluation.domain.enums import CoverageStatus
from max.evaluation.domain.models import EvaluationCase, EvaluationCoverage

ALL_MAX_SUBSYSTEMS = [
    "conversation",
    "runtime",
    "reasoning",
    "tasks",
    "agents",
    "tools",
    "permissions",
    "computer",
    "filesystem",
    "terminal",
    "applications",
    "browser",
    "web_intelligence",
    "coding",
    "developer",
    "documents",
    "vision",
    "speech",
    "notifications",
    "scheduler",
    "integrations",
    "proactive_intelligence",
    "personalization",
    "security",
    "reliability",
    "performance",
]


class EvaluationCoverageService:
    """Calculates subsystem evaluation coverage across dataset cases."""

    def calculate_coverage(self, cases: list[EvaluationCase]) -> list[EvaluationCoverage]:
        """Compute coverage status per MAX subsystem."""
        subsystem_case_counts: dict[str, int] = {sub: 0 for sub in ALL_MAX_SUBSYSTEMS}

        for case in cases:
            tags_lower = [t.lower() for t in case.tags]
            target_str = case.target_type.value.lower()

            for sub in ALL_MAX_SUBSYSTEMS:
                if sub in tags_lower or sub in target_str or case.evaluation_type.value.lower() == sub:
                    subsystem_case_counts[sub] += 1

        coverage_list: list[EvaluationCoverage] = []
        total_cases = len(cases)

        for sub, count in subsystem_case_counts.items():
            if count == 0:
                cov_status = CoverageStatus.NOT_COVERED
                pct = 0.0
            elif count < 3:
                cov_status = CoverageStatus.PARTIALLY_COVERED
                pct = round((count / max(1, total_cases)) * 100.0, 1)
            else:
                cov_status = CoverageStatus.COVERED
                pct = round((count / max(1, total_cases)) * 100.0, 1)

            coverage_list.append(
                EvaluationCoverage(
                    subsystem=sub,
                    status=cov_status,
                    total_cases=total_cases,
                    evaluated_cases=count,
                    coverage_percentage=pct,
                )
            )

        return coverage_list
