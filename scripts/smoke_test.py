"""Automated Infrastructure Smoke Test Script for MAX Deployment Verification."""

import argparse
import json
import sys
import urllib.request
import urllib.error


def run_smoke_tests(base_url: str) -> bool:
    """Execute smoke test suite against target MAX deployment instance."""
    base_url = base_url.rstrip("/")
    print(f"Executing MAX Infrastructure Smoke Tests against: {base_url}")
    passed = 0
    failed = 0

    endpoints = [
        ("/", "Service Identity Endpoint"),
        ("/health", "Liveness Probe"),
        ("/ready", "System Readiness Probe"),
        ("/api/v1/infrastructure/status", "Infrastructure Deployment Status"),
        ("/api/v1/infrastructure/metrics", "Infrastructure System Resource Metrics"),
        ("/api/v1/infrastructure/gpu", "GPU Hardware Acceleration Status"),
        ("/api/v1/infrastructure/secrets/rotation", "Secret Rotation Audit Inventory"),
        ("/api/v1/infrastructure/storage/presigned-url?object_name=test.txt", "Presigned Storage URL Generator"),
    ]

    for path, description in endpoints:
        url = f"{base_url}{path}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MAX-SmokeTest/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                status_code = resp.getcode()
                body = resp.read().decode("utf-8")
                data = json.loads(body)

                if status_code in (200, 201) and (data.get("success") is True or "status" in data):
                    print(f"  [PASS] {description} ({path}) -> HTTP {status_code}")
                    passed += 1
                else:
                    print(f"  [FAIL] {description} ({path}) -> Unexpected response body: {body[:100]}")
                    failed += 1
        except Exception as exc:
            print(f"  [FAIL] {description} ({path}) -> Error: {exc}")
            failed += 1

    print("\n--------------------------------------------------")
    print(f"Smoke Test Summary: {passed} PASSED, {failed} FAILED")
    print("--------------------------------------------------")

    return failed == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MAX Infrastructure Smoke Test Utility")
    parser.add_argument("--host", default="http://localhost:8000", help="Base URL of deployed MAX instance")
    args = parser.parse_args()

    success = run_smoke_tests(args.host)
    sys.exit(0 if success else 1)
