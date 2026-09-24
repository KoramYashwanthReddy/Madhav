"""Definition service managing evaluation definitions for Module 32."""

import logging
from typing import Any

from max.evaluation.domain.enums import EvaluationDimension, EvaluationType, EvaluatorType
from max.evaluation.domain.exceptions import EvaluationDefinitionNotFoundError
from max.evaluation.domain.models import EvaluationDefinition
from max.evaluation.repositories.interfaces import EvaluationDefinitionRepository

logger = logging.getLogger(__name__)


class EvaluationDefinitionService:
    """Manages formal evaluation definitions and parameters."""

    def __init__(self, definition_repo: EvaluationDefinitionRepository) -> None:
        self.definition_repo = definition_repo

    async def create_definition(
        self,
        name: str,
        dataset_id: str,
        evaluation_type: EvaluationType = EvaluationType.QUALITY,
        dataset_version: str = "1.0.0",
        dimensions: list[EvaluationDimension] | None = None,
        evaluator_types: list[EvaluatorType] | None = None,
        thresholds: dict[str, float] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EvaluationDefinition:
        """Create a new evaluation definition."""
        defn = EvaluationDefinition(
            name=name,
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            evaluation_type=evaluation_type,
            dimensions=dimensions or [EvaluationDimension.CORRECTNESS],
            evaluator_types=evaluator_types or [EvaluatorType.DETERMINISTIC],
            thresholds=thresholds or {"pass_rate": 0.8},
            metadata=metadata or {},
        )
        return await self.definition_repo.save(defn)

    async def get_definition(self, definition_id: str) -> EvaluationDefinition:
        """Fetch definition by ID."""
        defn = await self.definition_repo.get_by_id(definition_id)
        if defn is None:
            raise EvaluationDefinitionNotFoundError(f"Evaluation definition '{definition_id}' not found.")
        return defn

    async def list_definitions(self, limit: int = 100) -> list[EvaluationDefinition]:
        """List all definitions."""
        return await self.definition_repo.list_all(limit=limit)
