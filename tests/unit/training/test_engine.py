"""Unit tests for Training Engine, Checkpointing, and Job State Machine."""

import os

from max.training.domain import JobStatus, TrainingConfig, TrainingJob
from max.training.engine import CheckpointManager, MockTrainingBackend, TrainingJobService


def test_checkpoint_creation() -> None:
    chk_mgr = CheckpointManager()
    artifact = chk_mgr.create_checkpoint(job_id="test_job_1", step=50, loss=1.23)

    assert artifact.artifact_id.startswith("art_chk_")
    assert artifact.type == "CHECKPOINT"
    assert os.path.exists(artifact.filepath)
    assert artifact.size_bytes > 0


def test_mock_training_backend_execution() -> None:
    backend = MockTrainingBackend()
    config = TrainingConfig(
        model_id="max-small-base",
        base_model_path="models/max-small",
        dataset_id="ds_123",
        max_steps=20,
        checkpoint_steps=10,
    )
    job = TrainingJob(
        job_id="test_mock_job_1",
        dataset_id="ds_123",
        dataset_version="v1",
        base_model_id="max-small-base",
        config=config,
    )

    result_job = backend.execute_job(job)

    assert result_job.status in (JobStatus.EVALUATING, JobStatus.COMPLETED)
    assert result_job.current_step == 20
    assert result_job.progress_percent == 100.0
    assert len(result_job.metrics) == 20
    assert len(result_job.artifacts) > 0


def test_training_job_service_lifecycle() -> None:
    job_svc = TrainingJobService()
    config = TrainingConfig(
        model_id="max-small-base",
        base_model_path="models/max-small",
        dataset_id="ds_123",
        max_steps=10,
        checkpoint_steps=10,
    )
    job = job_svc.create_job(dataset_id="ds_123", base_model_id="max-small-base", config=config)
    assert job.status == JobStatus.QUEUED

    ran_job = job_svc.run_job(job.job_id)
    assert ran_job.status == JobStatus.COMPLETED
