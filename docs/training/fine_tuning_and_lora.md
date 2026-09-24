# Fine-Tuning, LoRA / QLoRA Hyperparameters & Resource Safety

## Supported Fine-Tuning Methods
1. **Supervised Fine-Tuning (SFT)**: Full or parameter-efficient fine-tuning on instruction datasets.
2. **LoRA (Low-Rank Adaptation)**: Injects trainable rank-decomposition matrices (`rank`, `alpha`, `dropout`, `target_modules`).
3. **QLoRA (4-Bit Quantized LoRA)**: Combines 4-bit NormalFloat (NF4) quantization with double quantization for low VRAM consumption on RTX 3050 (6GB VRAM).
4. **Full Fine-Tuning**: Available when hardware resources permit.

## Target Hardware Adaptation (RTX 3050 6GB)
Development machine resource limits:
- RTX 3050 (6GB VRAM)
- 24GB System RAM
- Ryzen 5 CPU

Module 40 automatically applies gradient accumulation, gradient checkpointing, sequence length limits, and 4-bit QLoRA to execute fine-tuning within host VRAM boundaries.

## Pre-Flight Resource Estimation & Pre-Execution Safety
Before initiating a training job, `ResourceEstimationService` estimates peak VRAM, system RAM, and disk requirements. If estimated requirements exceed host capabilities, the job fails safely in pre-flight before executing.
