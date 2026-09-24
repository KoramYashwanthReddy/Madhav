"""Services package for Module 32 — Evaluation System."""

from max.evaluation.services.coverage_service import EvaluationCoverageService
from max.evaluation.services.dataset_service import EvaluationDatasetService
from max.evaluation.services.definition_service import EvaluationDefinitionService
from max.evaluation.services.evaluation_service import EvaluationService
from max.evaluation.services.execution_service import EvaluationExecutionService
from max.evaluation.services.failure_analysis_service import FailureAnalysisService
from max.evaluation.services.regression_service import RegressionDetectionService
from max.evaluation.services.report_service import EvaluationReportService

__all__ = [
    "EvaluationDatasetService",
    "EvaluationDefinitionService",
    "FailureAnalysisService",
    "RegressionDetectionService",
    "EvaluationCoverageService",
    "EvaluationReportService",
    "EvaluationExecutionService",
    "EvaluationService",
]
