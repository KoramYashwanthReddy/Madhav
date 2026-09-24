"""Unit tests for Model Promotion, Evaluation Benchmark, and Rollback."""

from max.training.domain import ModelArtifact, PromotionStatus, TrainingConfig, TrainingJob
from max.training.evaluation import TrainingEvaluationService
from max.training.promotion import ModelPromotionService


def test_evaluation_service() -> None:
    eval_svc = TrainingEvaluationService()
    job = TrainingJob(
        job_id="job_eval_1",
        dataset_id="ds_123",
        dataset_version="v1",
        base_model_id="max-small-base",
        config=TrainingConfig(model_id="max-small-base", base_model_path="m", dataset_id="ds_123"),
    )
    report = eval_svc.evaluate_job(job)

    assert report.candidate_score > 0.0
    assert report.baseline_score > 0.0
    assert report.recommendation in ("APPROVE_PROMOTION", "REJECT_REGRESSION")


def test_model_promotion_and_rollback() -> None:
    prom_svc = ModelPromotionService()
    job = TrainingJob(
        job_id="job_prom_1",
        dataset_id="ds_123",
        dataset_version="v1",
        base_model_id="max-small-base",
        config=TrainingConfig(model_id="max-small-base", base_model_path="m", dataset_id="ds_123"),
        artifacts=[
            ModelArtifact(
                artifact_id="art_1",
                job_id="job_prom_1",
                type="ADAPTER",
                filepath="artifacts/adapter.safetensors",
                checksum_sha256="abc123hash",
                created_at="2026-09-24T00:00:00Z",
            )
        ],
    )

    # Approve model
    record = prom_svc.approve_model(job, user_id="admin_user")
    assert record.status == PromotionStatus.APPROVED

    # Promote model
    promoted = prom_svc.promote_to_production(record)
    assert promoted.status == PromotionStatus.PROMOTED

    # Rollback model
    rolled_back = prom_svc.rollback_model(promoted)
    assert rolled_back.status == PromotionStatus.ROLLED_BACK
