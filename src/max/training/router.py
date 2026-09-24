"""FastAPI Router for Module 40 — AI Training, Fine-Tuning & Model Improvement endpoints."""

from fastapi import APIRouter, Body, Depends, Path, Query
from pydantic import BaseModel, Field

from max.core.request_id import get_request_id
from max.core.responses import APIResponse
from max.training.domain import (
    Dataset,
    ResourceEstimation,
    TrainingConfig,
    TrainingHardwareProfile,
    TrainingJob,
    TrainingSample,
    ValidationReport,
)
from max.training.evaluation import EvaluationComparisonReport
from max.training.promotion import ModelPromotionRecord
from max.training.service import TrainingService, get_training_service

router = APIRouter(prefix="/training", tags=["AI Training & Fine-Tuning"])


class CreateDatasetRequest(BaseModel):
    """Request payload for dataset creation."""

    name: str = Field(..., description="Dataset name")
    description: str = Field(default="", description="Dataset description")
    samples: list[TrainingSample] | None = Field(default=None, description="Initial training samples")


class ValidateSamplesRequest(BaseModel):
    """Request payload for sample validation."""

    samples: list[TrainingSample] = Field(..., description="Sample list to validate")


class CreateJobRequest(BaseModel):
    """Request payload for enqueuing a training job."""

    dataset_id: str = Field(..., description="Training dataset ID")
    base_model_id: str = Field(..., description="Base model ID")
    config: TrainingConfig = Field(..., description="Training hyperparameters configuration")


class EvaluateJobRequest(BaseModel):
    """Request payload for evaluating candidate job."""

    baseline_model_id: str = Field(default="max-small-base", description="Baseline model ID for benchmark comparison")


@router.get("/hardware", response_model=APIResponse[TrainingHardwareProfile])
async def get_hardware_profile(
    svc: TrainingService = Depends(get_training_service),
) -> APIResponse[TrainingHardwareProfile]:
    """Retrieve host CPU, RAM, CUDA, and GPU hardware profile capabilities."""
    hw = svc.get_hardware_profile()
    return APIResponse(
        success=True,
        data=hw,
        request_id=get_request_id(),
    )


@router.post("/resources/estimate", response_model=APIResponse[ResourceEstimation])
async def estimate_resources(
    config: TrainingConfig,
    svc: TrainingService = Depends(get_training_service),
) -> APIResponse[ResourceEstimation]:
    """Estimate peak VRAM, RAM, disk, and duration requirements for training config."""
    est = svc.estimate_resources(config)
    return APIResponse(
        success=True,
        data=est,
        request_id=get_request_id(),
    )


@router.post("/datasets", response_model=APIResponse[Dataset])
async def create_dataset(
    req: CreateDatasetRequest,
    svc: TrainingService = Depends(get_training_service),
) -> APIResponse[Dataset]:
    """Create new dataset entity with versioning and checksum computation."""
    ds = svc.create_dataset(name=req.name, description=req.description, samples=req.samples)
    return APIResponse(
        success=True,
        data=ds,
        request_id=get_request_id(),
    )


@router.post("/datasets/validate", response_model=APIResponse[ValidationReport])
async def validate_samples(
    req: ValidateSamplesRequest,
    svc: TrainingService = Depends(get_training_service),
) -> APIResponse[ValidationReport]:
    """Validate sample schema compliance, token distribution, and cleanliness."""
    val = svc.validate_samples(req.samples)
    return APIResponse(
        success=True,
        data=val,
        request_id=get_request_id(),
    )


@router.post("/jobs", response_model=APIResponse[TrainingJob])
async def create_job(
    req: CreateJobRequest,
    svc: TrainingService = Depends(get_training_service),
) -> APIResponse[TrainingJob]:
    """Pre-flight validate resource feasibility and enqueue new training job."""
    job = svc.create_job(dataset_id=req.dataset_id, base_model_id=req.base_model_id, config=req.config)
    return APIResponse(
        success=True,
        data=job,
        request_id=get_request_id(),
    )


@router.post("/jobs/{job_id}/run", response_model=APIResponse[TrainingJob])
async def run_job(
    job_id: str = Path(..., description="Target job ID"),
    svc: TrainingService = Depends(get_training_service),
) -> APIResponse[TrainingJob]:
    """Execute training job using GPU/CPU execution backend."""
    job = svc.run_job(job_id=job_id)
    return APIResponse(
        success=job.status.value != "FAILED",
        data=job,
        request_id=get_request_id(),
    )


@router.get("/jobs/{job_id}", response_model=APIResponse[TrainingJob])
async def get_job(
    job_id: str = Path(..., description="Target job ID"),
    svc: TrainingService = Depends(get_training_service),
) -> APIResponse[TrainingJob]:
    """Retrieve job progress, metrics, and artifact metadata."""
    job = svc.get_job(job_id=job_id)
    return APIResponse(
        success=True,
        data=job,
        request_id=get_request_id(),
    )


@router.post("/jobs/{job_id}/cancel", response_model=APIResponse[TrainingJob])
async def cancel_job(
    job_id: str = Path(..., description="Target job ID"),
    svc: TrainingService = Depends(get_training_service),
) -> APIResponse[TrainingJob]:
    """Cancel queued or running job and release GPU reservation lock."""
    job = svc.cancel_job(job_id=job_id)
    return APIResponse(
        success=True,
        data=job,
        request_id=get_request_id(),
    )


@router.post("/jobs/{job_id}/evaluate", response_model=APIResponse[EvaluationComparisonReport])
async def evaluate_job(
    req: EvaluateJobRequest = Body(default_factory=EvaluateJobRequest),
    job_id: str = Path(..., description="Target job ID"),
    svc: TrainingService = Depends(get_training_service),
) -> APIResponse[EvaluationComparisonReport]:
    """Evaluate candidate model against baseline benchmark using Module 32 Evaluation System."""
    report = svc.evaluate_job(job_id=job_id, baseline_model_id=req.baseline_model_id)
    return APIResponse(
        success=True,
        data=report,
        request_id=get_request_id(),
    )


@router.post("/jobs/{job_id}/approve", response_model=APIResponse[ModelPromotionRecord])
async def approve_model(
    job_id: str = Path(..., description="Target job ID"),
    user_id: str = Query("user_admin", description="Approving admin entity ID"),
    svc: TrainingService = Depends(get_training_service),
) -> APIResponse[ModelPromotionRecord]:
    """Approve candidate model for promotion after evaluation and security verification."""
    record = svc.approve_model(job_id=job_id, user_id=user_id)
    return APIResponse(
        success=True,
        data=record,
        request_id=get_request_id(),
    )


@router.post("/promotions/promote", response_model=APIResponse[ModelPromotionRecord])
async def promote_to_production(
    record: ModelPromotionRecord,
    svc: TrainingService = Depends(get_training_service),
) -> APIResponse[ModelPromotionRecord]:
    """Promote approved model to active production inference target."""
    updated = svc.promote_to_production(record)
    return APIResponse(
        success=True,
        data=updated,
        request_id=get_request_id(),
    )


@router.post("/promotions/rollback", response_model=APIResponse[ModelPromotionRecord])
async def rollback_model(
    record: ModelPromotionRecord,
    svc: TrainingService = Depends(get_training_service),
) -> APIResponse[ModelPromotionRecord]:
    """Roll back promoted model while preserving immutable model artifacts."""
    updated = svc.rollback_model(record)
    return APIResponse(
        success=True,
        data=updated,
        request_id=get_request_id(),
    )
