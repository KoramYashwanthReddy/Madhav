"""Verification script executing Configuration Diagnostics, Ruff, MyPy, and Pytest."""

import subprocess
import sys


def run_step(step_name: str, command: list[str]) -> bool:
    """Execute a verification command step and return success boolean."""
    print("\n==================================================")
    print(f"Running Step: {step_name}")
    print(f"Command: {' '.join(command)}")
    print("==================================================")

    result = subprocess.run(command)
    if result.returncode == 0:
        print(f"[PASS] {step_name} PASSED.")
        return True
    else:
        print(f"[FAIL] {step_name} FAILED (exit code {result.returncode}).")
        return False


def main() -> None:
    """Run full foundation verification suite."""
    steps: list[tuple[str, list[str]]] = [
        ("Configuration Diagnostics", [sys.executable, "-m", "madhav.config"]),
        ("Ruff Linter", [sys.executable, "-m", "ruff", "check", "."]),
        ("MyPy Type Checker", [sys.executable, "-m", "mypy", "src"]),
        ("Pytest Test Suite", [sys.executable, "-m", "pytest"]),
    ]

    failed_steps: list[str] = []

    for name, cmd in steps:
        success = run_step(name, cmd)
        if not success:
            failed_steps.append(name)

    print("\n==================================================")
    if failed_steps:
        print(f"[FAIL] VERIFICATION FAILED! Failed steps: {', '.join(failed_steps)}")
        sys.exit(1)
    else:
        print("[PASS] ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")
        sys.exit(0)


if __name__ == "__main__":
    main()
