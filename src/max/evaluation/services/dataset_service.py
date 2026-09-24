"""Dataset service managing evaluation datasets and golden datasets for Module 32."""

import logging
from datetime import UTC, datetime

from max.evaluation.domain.exceptions import DatasetNotFoundError
from max.evaluation.domain.models import EvaluationCase, EvaluationDataset, EvaluationDatasetVersion
from max.evaluation.repositories.interfaces import EvaluationDatasetRepository

logger = logging.getLogger(__name__)


class EvaluationDatasetService:
    """Manages datasets, versions, and golden test cases."""

    def __init__(self, dataset_repo: EvaluationDatasetRepository) -> None:
        self.dataset_repo = dataset_repo

    async def create_dataset(
        self,
        name: str,
        description: str = "",
        owner_id: str = "default_owner",
        cases: list[EvaluationCase] | None = None,
        is_golden: bool = False,
        tags: list[str] | None = None,
    ) -> EvaluationDataset:
        """Create a new evaluation dataset."""
        dataset = EvaluationDataset(
            name=name,
            description=description,
            owner_id=owner_id,
            cases=cases or [],
            is_golden=is_golden,
            tags=tags or [],
        )
        return await self.dataset_repo.save(dataset)

    async def get_dataset(self, dataset_id: str) -> EvaluationDataset:
        """Fetch dataset by ID."""
        ds = await self.dataset_repo.get_by_id(dataset_id)
        if ds is None:
            raise DatasetNotFoundError(f"Dataset '{dataset_id}' not found.")
        return ds

    async def list_datasets(self, limit: int = 100) -> list[EvaluationDataset]:
        """List all datasets."""
        return await self.dataset_repo.list_all(limit=limit)

    async def add_case_to_dataset(self, dataset_id: str, case: EvaluationCase) -> EvaluationDataset:
        """Add an evaluation case to a dataset."""
        ds = await self.get_dataset(dataset_id)
        ds.cases.append(case)
        ds.updated_at = datetime.now(UTC)
        return await self.dataset_repo.save(ds)

    async def create_version(self, dataset_id: str, version_tag: str) -> EvaluationDatasetVersion:
        """Create an immutable version snapshot of a dataset."""
        ds = await self.get_dataset(dataset_id)
        ds.version = version_tag
        await self.dataset_repo.save(ds)
        return EvaluationDatasetVersion(
            dataset_id=dataset_id,
            version_tag=version_tag,
            case_ids=[c.case_id for c in ds.cases],
            case_count=len(ds.cases),
        )
