"""Integration tests for Module 32 REST API endpoints."""

import pytest
from fastapi.testclient import TestClient

from max.evaluation.container import EvaluationContainer
from max.main import app


@pytest.fixture(autouse=True)
def reset_container():
    EvaluationContainer.reset_instance()
    yield
    EvaluationContainer.reset_instance()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_get_health_and_summary_endpoints(client: TestClient):
    """Test GET /api/v1/evaluations/health and /summary."""
    health_res = client.get("/api/v1/evaluations/health")
    assert health_res.status_code == 200
    assert health_res.json()["enabled"] is True

    summary_res = client.get("/api/v1/evaluations/summary")
    assert summary_res.status_code == 200
    assert "total_datasets" in summary_res.json()


def test_get_coverage_endpoint(client: TestClient):
    """Test GET /api/v1/evaluations/coverage."""
    res = client.get("/api/v1/evaluations/coverage")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 20


def test_dataset_crud_endpoints(client: TestClient):
    """Test POST, GET /api/v1/evaluations/datasets."""
    payload = {
        "name": "test_api_dataset",
        "description": "API Test Dataset",
        "cases": [
            {
                "name": "Case 1",
                "input_prompt": "Hello",
                "expected_output": "Hello",
            }
        ],
    }
    create_res = client.post("/api/v1/evaluations/datasets", json=payload)
    assert create_res.status_code == 201
    ds_id = create_res.json()["dataset_id"]

    get_res = client.get(f"/api/v1/evaluations/datasets/{ds_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "test_api_dataset"

    list_res = client.get("/api/v1/evaluations/datasets")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_run_creation_and_execution_endpoints(client: TestClient):
    """Test POST /api/v1/evaluations/runs and execute."""
    # Pre-seeded golden dataset ID: ds_golden_sample
    run_payload = {
        "dataset_id": "ds_golden_sample",
        "target_type": "AI_RUNTIME",
    }
    create_run_res = client.post("/api/v1/evaluations/runs", json=run_payload)
    assert create_run_res.status_code == 201
    run_id = create_run_res.json()["run_id"]

    exec_res = client.post(f"/api/v1/evaluations/runs/{run_id}/execute")
    assert exec_res.status_code == 200
    assert exec_res.json()["status"] == "COMPLETED"

    report_res = client.get(f"/api/v1/evaluations/runs/{run_id}/report")
    assert report_res.status_code == 200
    assert report_res.json()["overall_pass_rate"] > 0.0


def test_run_comparison_endpoint(client: TestClient):
    """Test POST /api/v1/evaluations/compare."""
    # Create two runs
    run_payload = {"dataset_id": "ds_golden_sample"}
    r1_id = client.post("/api/v1/evaluations/runs", json=run_payload).json()["run_id"]
    r2_id = client.post("/api/v1/evaluations/runs", json=run_payload).json()["run_id"]

    client.post(f"/api/v1/evaluations/runs/{r1_id}/execute")
    client.post(f"/api/v1/evaluations/runs/{r2_id}/execute")

    compare_res = client.post(
        "/api/v1/evaluations/compare",
        json={"baseline_run_id": r1_id, "candidate_run_id": r2_id},
    )
    assert compare_res.status_code == 200
    assert "baseline_pass_rate" in compare_res.json()
