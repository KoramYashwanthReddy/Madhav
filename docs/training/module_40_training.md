# Module 40 — AI Training, Fine-Tuning & Model Improvement

## Overview
Module 40 provides provider-neutral AI training, fine-tuning, dataset versioning, LoRA/QLoRA adaptation, evaluation integration, and controlled model promotion for the MAX Personal AI System.

## Architecture Highlights
- **Resource Detection & Pre-Flight Estimation (`hardware.py`)**: Detects CPU, RAM, CUDA, and VRAM. Estimates VRAM/RAM/disk usage before training and blocks unfeasible jobs.
- **Dataset Management & Validation (`datasets.py`)**: Dataset versioning (v1, v2), SHA-256 checksums, JSONL/JSON/CSV format parsing, deduplication, leakage detection, and prompt injection data poisoning protection.
- **Training Engine & Checkpointing (`engine.py`)**: Supports SFT, LoRA, QLoRA, and Full Fine-tuning. Provides `MockTrainingBackend` and `HuggingFaceTrainingBackend` with safe `safetensors` artifact generation.
- **Evaluation Integration (`evaluation.py`)**: Integrates Module 32 Evaluation System for candidate vs baseline benchmark score comparison.
- **Controlled Model Promotion (`promotion.py`)**: Enforces explicit approval policy, Module 05 Model Registry registration, Module 39 storage backups, and safe rollback capabilities.
- **API Endpoints (`router.py`)**: REST API endpoints under `/api/v1/training/*`.
- **Operational CLI Tools**: `scripts/training_env_check.py` and `scripts/run_training.py`.
