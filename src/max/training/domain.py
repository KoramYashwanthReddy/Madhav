"""Domain models and data structures for Module 40 — AI Training & Fine-Tuning."""

import enum
from typing import Any
from pydantic import BaseModel, Field

from max.version import VERSION


class DatasetStatus(str, enum.Enum):
    """Lifecycle status for training datasets."""

    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    VALID = "VALID"
    INVALID = "INVALID"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class TrainingMethod(str, enum.Enum):
    """Supported model fine-tuning and training methods."""

    SFT = "SFT"
    LORA = "LORA"
    QLORA = "QLORA"
    FULL_FINE_TUNE = "FULL_FINE_TUNE"
    CONTINUED_PRETRAINING = "CONTINUED_PRETRAINING"
    PREFERENCE_OPTIMIZATION = "PREFERENCE_OPTIMIZATION"


class JobStatus(str, enum.Enum):
    """Lifecycle state machine for training jobs."""

    QUEUED = "QUEUED"
    VALIDATING = "VALIDATING"
    PREPARING = "PREPARING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    STOPPED = "STOPPED"
    EVALUATING = "EVALUATING"
    PROMOTED = "PROMOTED"
    REJECTED = "REJECTED"


class JobPriority(str, enum.Enum):
    """Training job execution priority."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"


class PromotionStatus(str, enum.Enum):
    """Model promotion lifecycle state."""

    TRAINED = "TRAINED"
    EVALUATING = "EVALUATING"
    EVALUATED = "EVALUATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PROMOTED = "PROMOTED"
    ROLLED_BACK = "ROLLED_BACK"


class TrainingSample(BaseModel):
    """Normalized training instruction / conversational sample."""

    instruction: str | None = Field(default=None, description="Task instruction prompt")
    input_text: str | None = Field(default=None, description="Optional context input")
    output_text: str | None = Field(default=None, description="Expected target completion text")
    messages: list[dict[str, str]] | None = Field(
        default=None, description="Conversational message history [{'role': 'user', 'content': '...'}]"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Sample origin metadata and provenance tags")


class DatasetStats(BaseModel):
    """Calculated dataset quality and token statistics."""

    sample_count: int = Field(default=0, description="Total record count")
    duplicate_count: int = Field(default=0, description="Duplicate sample count")
    empty_count: int = Field(default=0, description="Empty sample count")
    avg_tokens: float = Field(default=0.0, description="Average token count per sample")
    min_tokens: int = Field(default=0, description="Minimum token count")
    max_tokens: int = Field(default=0, description="Maximum token count")
    input_output_ratio: float = Field(default=1.0, description="Average ratio of input tokens to output tokens")
    invalid_count: int = Field(default=0, description="Invalid sample count")


class ValidationReport(BaseModel):
    """Validation report detailing dataset cleanliness, schema compliance, and errors."""

    valid: bool = Field(default=True, description="Whether dataset is valid for training")
    stats: DatasetStats = Field(default_factory=DatasetStats, description="Dataset statistics")
    errors: list[str] = Field(default_factory=list, description="Validation error messages")
    warnings: list[str] = Field(default_factory=list, description="Quality warning messages")
    truncation_count: int = Field(default=0, description="Number of samples exceeding max sequence limit")


class DatasetVersion(BaseModel):
    """Versioned iteration of a training dataset."""

    dataset_id: str = Field(..., description="Parent dataset ID")
    version: str = Field(..., description="Version string (e.g. v1, v2)")
    checksum_sha256: str = Field(..., description="SHA-256 integrity checksum")
    record_count: int = Field(default=0, description="Total sample count in version")
    train_count: int = Field(default=0, description="Train split record count")
    val_count: int = Field(default=0, description="Validation split record count")
    test_count: int = Field(default=0, description="Test split record count")
    split_seed: int = Field(default=42, description="Deterministic seed used for train/val/test splitting")
    split_ratio: str = Field(default="80/10/10", description="Train/val/test split ratio")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    stats: DatasetStats = Field(default_factory=DatasetStats, description="Quality stats")


class Dataset(BaseModel):
    """Training dataset entity metadata."""

    dataset_id: str = Field(..., description="Unique dataset identifier")
    name: str = Field(..., description="Dataset display name")
    description: str = Field(default="", description="Dataset description")
    owner_id: str = Field(default="system", description="Owner or creator user ID")
    status: DatasetStatus = Field(default=DatasetStatus.DRAFT, description="Dataset lifecycle status")
    format: str = Field(default="JSONL", description="File format (JSONL, JSON, CSV)")
    source: str = Field(default="AUTHORIZED_USER", description="Data provenance source")
    current_version: str = Field(default="v1", description="Latest version string")
    versions: list[DatasetVersion] = Field(default_factory=list, description="Dataset version history")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    updated_at: str = Field(..., description="ISO 8601 modification timestamp")


class LoRAConfig(BaseModel):
    """Low-Rank Adaptation (LoRA) hyperparameters."""

    rank: int = Field(default=8, ge=1, le=256, description="LoRA rank dimension (r)")
    alpha: int = Field(default=16, ge=1, le=512, description="LoRA alpha scaling factor")
    dropout: float = Field(default=0.05, ge=0.0, le=0.5, description="LoRA dropout rate")
    target_modules: list[str] = Field(
        default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj"],
        description="Target module projection layers",
    )
    bias: str = Field(default="none", description="Bias type (none, all, lora_only)")
    task_type: str = Field(default="CAUSAL_LM", description="PEFT task type")


class QLoRAConfig(BaseModel):
    """Quantized LoRA (QLoRA) 4-bit hyperparameters."""

    bits: int = Field(default=4, description="Quantization bit precision (4-bit)")
    quant_type: str = Field(default="nf4", description="Quantization data type (nf4, fp4)")
    double_quant: bool = Field(default=True, description="Enable double quantization")
    compute_dtype: str = Field(default="float16", description="Compute precision data type")
    lora: LoRAConfig = Field(default_factory=LoRAConfig, description="Associated LoRA adapter config")


class TrainingConfig(BaseModel):
    """Comprehensive training experiment hyperparameter configuration."""

    model_id: str = Field(..., description="Base model ID from Module 05")
    base_model_path: str = Field(..., description="Base model artifact path or HuggingFace ID")
    dataset_id: str = Field(..., description="Training dataset ID")
    dataset_version: str = Field(default="v1", description="Dataset version string")
    method: TrainingMethod = Field(default=TrainingMethod.LORA, description="Training method")
    epochs: int = Field(default=3, ge=1, le=100, description="Training epochs")
    max_steps: int = Field(default=100, ge=1, le=100000, description="Maximum training steps")
    batch_size: int = Field(default=2, ge=1, le=128, description="Per-device train batch size")
    gradient_accumulation_steps: int = Field(default=4, ge=1, le=64, description="Gradient accumulation steps")
    learning_rate: float = Field(default=2e-4, ge=1e-7, le=1e-1, description="Learning rate")
    warmup_ratio: float = Field(default=0.03, ge=0.0, le=0.5, description="Linear warmup ratio")
    weight_decay: float = Field(default=0.01, ge=0.0, le=0.5, description="Weight decay")
    max_sequence_length: int = Field(default=1024, ge=64, le=8192, description="Maximum sequence length")
    precision: str = Field(default="fp16", description="Training precision (fp32, fp16, bf16)")
    gradient_checkpointing: bool = Field(default=True, description="Enable gradient checkpointing to save VRAM")
    lora: LoRAConfig = Field(default_factory=LoRAConfig, description="LoRA configuration")
    qlora: QLoRAConfig = Field(default_factory=QLoRAConfig, description="QLoRA configuration")
    seed: int = Field(default=42, description="Deterministic random seed")
    checkpoint_steps: int = Field(default=50, ge=10, le=1000, description="Save checkpoint every N steps")


class TrainingHardwareProfile(BaseModel):
    """Host CPU, RAM, and GPU hardware capability profile."""

    os_name: str = Field(..., description="Host OS (Windows, Linux)")
    cpu_cores: int = Field(..., description="Available CPU logical cores")
    ram_total_gb: float = Field(..., description="Total system RAM in GB")
    ram_free_gb: float = Field(..., description="Free system RAM in GB")
    gpu_available: bool = Field(default=False, description="Whether CUDA GPU is detected")
    gpu_name: str | None = Field(default=None, description="GPU model name (e.g. RTX 3050 6GB)")
    vram_total_mb: float = Field(default=0.0, description="Total VRAM in MB")
    vram_free_mb: float = Field(default=0.0, description="Available free VRAM in MB")
    cuda_version: str | None = Field(default=None, description="Installed CUDA driver version")
    pytorch_version: str = Field(..., description="Installed PyTorch version")
    pytorch_cuda_available: bool = Field(default=False, description="Whether PyTorch supports CUDA")


class ResourceEstimation(BaseModel):
    """Estimated resource requirements for a training job."""

    estimated_vram_mb: float = Field(..., description="Estimated peak VRAM requirement in MB")
    estimated_ram_gb: float = Field(..., description="Estimated RAM requirement in GB")
    estimated_disk_gb: float = Field(..., description="Estimated disk space requirement for checkpoints in GB")
    estimated_duration_minutes: float = Field(..., description="Estimated training runtime in minutes")
    is_feasible: bool = Field(default=True, description="Whether hardware profile meets estimated requirements")
    feasibility_reason: str | None = Field(default=None, description="Reason if training is not feasible")


class TrainingMetric(BaseModel):
    """Training loss, learning rate, and resource metric point."""

    step: int = Field(..., description="Global step index")
    epoch: float = Field(..., description="Epoch progress")
    loss: float = Field(..., description="Training loss value")
    learning_rate: float = Field(..., description="Current learning rate")
    vram_allocated_mb: float = Field(default=0.0, description="Allocated VRAM in MB")
    cpu_percent: float = Field(default=0.0, description="CPU usage percent")
    timestamp: str = Field(..., description="ISO 8601 timestamp")


class ModelArtifact(BaseModel):
    """Registered artifact produced by a training job."""

    artifact_id: str = Field(..., description="Unique artifact identifier")
    job_id: str = Field(..., description="Originating training job ID")
    type: str = Field(..., description="Artifact type (CHECKPOINT, ADAPTER, MERGED_MODEL, TOKENIZER)")
    filepath: str = Field(..., description="Path to artifact file or directory")
    size_bytes: int = Field(default=0, description="Artifact size in bytes")
    checksum_sha256: str = Field(..., description="SHA-256 integrity checksum")
    format: str = Field(default="safetensors", description="Serialization format")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")


class TrainingJob(BaseModel):
    """Training job entity tracking state, progress, and metrics."""

    job_id: str = Field(..., description="Unique training job ID")
    owner_id: str = Field(default="system", description="Owner user ID")
    dataset_id: str = Field(..., description="Dataset ID")
    dataset_version: str = Field(..., description="Dataset version string")
    base_model_id: str = Field(..., description="Base model ID")
    config: TrainingConfig = Field(..., description="Training configuration")
    status: JobStatus = Field(default=JobStatus.QUEUED, description="Lifecycle status")
    progress_percent: float = Field(default=0.0, description="Job completion percentage")
    current_step: int = Field(default=0, description="Current step")
    total_steps: int = Field(default=100, description="Total target steps")
    current_loss: float | None = Field(default=None, description="Latest training loss")
    metrics: list[TrainingMetric] = Field(default_factory=list, description="Logged metric series")
    artifacts: list[ModelArtifact] = Field(default_factory=list, description="Output model artifacts")
    error_message: str | None = Field(default=None, description="Error message if job failed")
    started_at: str | None = Field(default=None, description="ISO 8601 start timestamp")
    completed_at: str | None = Field(default=None, description="ISO 8601 completion timestamp")
    last_heartbeat: str | None = Field(default=None, description="ISO 8601 worker heartbeat timestamp")


class TrainingExperiment(BaseModel):
    """Experiment tracking container linking dataset, configuration, metrics, and evaluation results."""

    experiment_id: str = Field(..., description="Unique experiment ID")
    name: str = Field(..., description="Experiment name")
    description: str = Field(default="", description="Hypothesis description")
    base_model_id: str = Field(..., description="Base model ID")
    dataset_id: str = Field(..., description="Dataset ID")
    job: TrainingJob = Field(..., description="Associated training job")
    promotion_status: PromotionStatus = Field(default=PromotionStatus.TRAINED, description="Promotion status")
    created_at: str = Field(..., description="ISO 8601 timestamp")


class TrainingEnvironment(BaseModel):
    """Recorded dependency versions and environment checksum for experiment reproducibility."""

    python_version: str = Field(..., description="Python version")
    pytorch_version: str = Field(..., description="PyTorch version")
    transformers_version: str = Field(default="4.38.0", description="Transformers version")
    peft_version: str = Field(default="0.8.0", description="PEFT version")
    trl_version: str = Field(default="0.7.0", description="TRL version")
    cuda_version: str | None = Field(default=None, description="CUDA driver version")
    env_checksum: str = Field(..., description="SHA-256 hash of dependency environment")


class TrainingReport(BaseModel):
    """Summary report generated at job completion for SRE review and Module 37 Admin Console."""

    experiment_id: str = Field(..., description="Experiment ID")
    job_id: str = Field(..., description="Job ID")
    status: JobStatus = Field(..., description="Final job status")
    duration_seconds: float = Field(..., description="Total runtime duration")
    final_loss: float | None = Field(default=None, description="Final training loss")
    artifacts_produced: int = Field(default=0, description="Total artifacts count")
    hardware: TrainingHardwareProfile = Field(..., description="Hardware profile used")
    environment: TrainingEnvironment = Field(..., description="Reproducibility environment metadata")
