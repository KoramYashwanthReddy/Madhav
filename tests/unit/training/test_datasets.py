"""Unit tests for Dataset Validation, Preprocessing, Versioning, and Leakage Detection."""

from max.training.datasets import (
    DataCleaner,
    DatasetService,
    DatasetValidationService,
    LeakageDetector,
)
from max.training.domain import DatasetStatus, TrainingSample


def test_dataset_cleaning_and_deduplication() -> None:
    s1 = TrainingSample(instruction=" Hello ", output_text=" World ")
    s2 = TrainingSample(instruction="Hello", output_text="World")

    c1 = DataCleaner.clean_sample(s1)
    assert c1 is not None
    assert c1.instruction == "Hello"
    assert c1.output_text == "World"

    dedup = DataCleaner.deduplicate([s1, s2])
    assert len(dedup) == 1


def test_leakage_detection() -> None:
    train_set = [TrainingSample(instruction="Task A", output_text="Ans A")]
    eval_set = [TrainingSample(instruction="Task A", output_text="Ans A"), TrainingSample(instruction="Task B", output_text="Ans B")]

    leakage_count = LeakageDetector.check_leakage(train_set, eval_set)
    assert leakage_count == 1


def test_dataset_validation() -> None:
    val_svc = DatasetValidationService()
    report = val_svc.validate_samples([
        TrainingSample(instruction="Test instruction", output_text="Test output text")
    ])

    assert report.valid is True
    assert report.stats.sample_count == 1
    assert report.stats.avg_tokens > 0


def test_dataset_creation_and_versioning() -> None:
    ds_svc = DatasetService()
    ds = ds_svc.create_dataset(
        name="Test Dataset Alpha",
        description="Dataset for unit testing",
        samples=[TrainingSample(instruction="Say Hi", output_text="Hello MAX")],
    )

    assert ds.dataset_id.startswith("ds_")
    assert ds.status == DatasetStatus.VALID
    assert ds.current_version == "v1"
    assert len(ds.versions) == 1
    assert ds.versions[0].record_count == 1
