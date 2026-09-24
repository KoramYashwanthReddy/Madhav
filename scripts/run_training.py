"""CLI utility for running end-to-end AI fine-tuning experiments."""

import argparse
import sys
from max.training.domain import LoRAConfig, TrainingConfig, TrainingMethod, TrainingSample
from max.training.service import get_training_service


def main() -> None:
    parser = argparse.ArgumentParser(description="MAX AI Training & Fine-Tuning CLI")
    parser.add_argument("--model", default="max-small-base", help="Base model ID")
    parser.add_argument("--method", default="LORA", choices=["SFT", "LORA", "QLORA", "FULL_FINE_TUNE"], help="Training method")
    parser.add_argument("--steps", type=int, default=50, help="Training steps")
    args = parser.parse_args()

    print("==================================================")
    print("MAX AI Fine-Tuning CLI Runner")
    print("==================================================")

    svc = get_training_service()

    # 1. Create Dataset
    ds = svc.create_dataset(
        name="CLI Instruction Set",
        description="Dataset created via run_training CLI",
        samples=[
            TrainingSample(
                instruction="Explain the role of Module 40 in MAX AI System.",
                input_text="Module 40 handles AI training, fine-tuning, and model improvement.",
                output_text="Module 40 provides provider-neutral fine-tuning, dataset versioning, LoRA/QLoRA adaptation, evaluation, and controlled promotion.",
            )
        ],
    )
    print(f"[1/5] Created Dataset: {ds.dataset_id} ({ds.name})")

    # 2. Build Training Config
    method_enum = TrainingMethod[args.method]
    config = TrainingConfig(
        model_id=args.model,
        base_model_path=f"models/{args.model}",
        dataset_id=ds.dataset_id,
        dataset_version="v1",
        method=method_enum,
        epochs=1,
        max_steps=args.steps,
        batch_size=2,
        max_sequence_length=512,
        lora=LoRAConfig(rank=8, alpha=16),
        checkpoint_steps=25,
    )

    # 3. Estimate Resources
    est = svc.estimate_resources(config)
    print(f"[2/5] Resource Estimate: VRAM={est.estimated_vram_mb}MB, RAM={est.estimated_ram_gb}GB, Duration={est.estimated_duration_minutes}min (Feasible: {est.is_feasible})")
    if not est.is_feasible:
        print(f"ERROR: Resource estimation failed: {est.feasibility_reason}")
        sys.exit(1)

    # 4. Enqueue and Run Job
    job = svc.create_job(dataset_id=ds.dataset_id, base_model_id=args.model, config=config)
    print(f"[3/5] Enqueued Training Job: {job.job_id}")

    job_result = svc.run_job(job.job_id)
    print(f"[4/5] Training Completed. Final Loss: {job_result.current_loss} (Artifacts: {len(job_result.artifacts)})")

    # 5. Evaluate Candidate Model
    eval_report = svc.evaluate_job(job_result.job_id)
    print(f"[5/5] Evaluation Score: {eval_report.candidate_score} vs Baseline {eval_report.baseline_score} (Recommendation: {eval_report.recommendation})")

    print("\n--------------------------------------------------")
    print("SUCCESS: Fine-Tuning Experiment Completed!")
    print("--------------------------------------------------")


if __name__ == "__main__":
    main()
