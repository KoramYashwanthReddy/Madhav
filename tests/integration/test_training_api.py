"""Integration tests for Module 40 — AI Training & Fine-Tuning API endpoints."""

import pytest
from fastapi.testclient import TestClient

from max.core.application import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_get_hardware_profile_api(client: TestClient) -> None:
    response = client.get("/api/v1/training/hardware")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "os_name" in data["data"]
    assert "cpu_cores" in data["data"]


def test_estimate_resources_api(client: TestClient) -> None:
    config_payload = {
        "model_id": "max-small-base",
        "base_model_path": "models/max-small",
        "dataset_id": "ds_123",
        "method": "LORA",
        "epochs": 1,
        "max_steps": 50,
        "batch_size": 2,
        "max_sequence_length": 512,
    }
    response = client.post("/api/v1/training/resources/estimate", json=config_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "estimated_vram_mb" in data["data"]


def test_create_dataset_and_validate_api(client: TestClient) -> None:
    # 1. Validate Samples
    samples_payload = {
        "samples": [
            {"instruction": "What is Module 40?", "output_text": "AI Training & Fine-Tuning Module."}
        ]
    }
    val_resp = client.post("/api/v1/training/datasets/validate", json=samples_payload)
    assert val_resp.status_code == 200
    assert val_resp.json()["data"]["valid"] is True

    # 2. Create Dataset
    ds_payload = {
        "name": "Integration Test Dataset",
        "description": "API Integration test set",
        "samples": samples_payload["samples"],
    }
    create_resp = client.post("/api/v1/training/datasets", json=ds_payload)
    assert create_resp.status_code == 200
    ds_data = create_resp.json()
    assert ds_data["success"] is True
    assert ds_data["data"]["dataset_id"].startswith("ds_")


def test_end_to_end_training_experiment_flow(client: TestClient) -> None:
    # 1. Create Dataset
    ds_resp = client.post(
        "/api/v1/training/datasets",
        json={
            "name": "E2E Dataset",
            "samples": [{"instruction": "E2E Task", "output_text": "E2E Result"}],
        },
    )
    dataset_id = ds_resp.json()["data"]["dataset_id"]

    # 2. Create Job
    job_payload = {
        "dataset_id": dataset_id,
        "base_model_id": "max-small-base",
        "config": {
            "model_id": "max-small-base",
            "base_model_path": "models/max-small",
            "dataset_id": dataset_id,
            "method": "LORA",
            "max_steps": 20,
            "checkpoint_steps": 10,
        },
    }
    create_job_resp = client.post("/api/v1/training/jobs", json=job_payload)
    assert create_job_resp.status_code == 200
    job_id = create_job_resp.json()["data"]["job_id"]

    # 3. Run Job
    run_resp = client.post(f"/api/v1/training/jobs/{job_id}/run")
    assert run_resp.status_code == 200
    ran_job = run_resp.json()["data"]
    assert ran_job["status"] in ("EVALUATING", "COMPLETED")

    # 4. Evaluate Job
    eval_resp = client.post(f"/api/v1/training/jobs/{job_id}/evaluate", json={"baseline_model_id": "max-small-base"})
    assert eval_resp.status_code == 200
    eval_report = eval_resp.json()["data"]
    assert eval_report["candidate_score"] > 0.0

    # 5. Approve Model
    appr_resp = client.post(f"/api/v1/training/jobs/{job_id}/approve?user_id=admin_user")
    assert appr_resp.status_code == 200
    record = appr_resp.json()["data"]
    assert record["status"] == "APPROVED"

    # 6. Promote Model
    prom_resp = client.post("/api/v1/training/promotions/promote", json=record)
    assert prom_resp.status_code == 200
    promoted = prom_resp.json()["data"]
    assert promoted["status"] == "PROMOTED"

    # 7. Rollback Model
    roll_resp = client.post("/api/v1/training/promotions/rollback", json=promoted)
    assert roll_resp.status_code == 200
    rolled_back = roll_resp.json()["data"]
    assert rolled_back["status"] == "ROLLED_BACK"
