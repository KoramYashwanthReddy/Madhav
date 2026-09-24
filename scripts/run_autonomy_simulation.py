"""CLI tool executing multi-step autonomous mission simulation and dry-run analysis."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from max.autonomy.domain import AutonomyLevel, MissionAction, ResourceBudget, RiskLevel
from max.autonomy.service import get_autonomy_service


def main() -> None:
    """Execute end-to-end simulated autonomous mission workflow."""
    print("=== Module 41: End-to-End Autonomous Mission Simulation ===")
    svc = get_autonomy_service()

    # 1. Create simulated mission
    mission = svc.create_mission(
        title="Simulated Code Review & Artifact Report Mission",
        objective="Analyze codebase files, generate review report, and store artifact safely.",
        autonomy_level=AutonomyLevel.SUPERVISED,
        allowed_scope=["data/*", "artifacts/*", "docs/*"],
        budget=ResourceBudget(max_execution_seconds=300, max_tool_calls=10),
        actions=[
            MissionAction(
                action_id="step_1",
                mission_id="sim_m1",
                step_number=1,
                tool_id="search_files",
                arguments={"pattern": "*.md", "path": "docs/autonomy"},
                risk_level=RiskLevel.LOW,
            ),
            MissionAction(
                action_id="step_2",
                mission_id="sim_m1",
                step_number=2,
                tool_id="create_draft",
                arguments={"path": "docs/autonomy/report.md", "file_path": "docs/autonomy/report.md"},
                risk_level=RiskLevel.MEDIUM,
            ),
        ],
    )

    print(f"[+] Created Mission '{mission.title}' (ID: {mission.mission_id})")

    # 2. Perform Pre-flight Dry-Run Analysis
    dry_run = svc.dry_run_mission(mission.mission_id)
    print("\n--- Dry-Run Pre-Flight Analysis ---")
    print(f"Total Steps: {dry_run['total_steps']} | Executable: {dry_run['is_executable']}")
    for st in dry_run["steps_analysis"]:
        print(f"  Step {st['step']}: Tool={st['tool_id']} | Risk={st['risk_level']} | Decision={st['reason']}")

    # 3. Execute Mission Loop
    print("\n--- Executing Autonomous Mission Loop ---")
    res = svc.run_mission(mission.mission_id)

    print("\n--- Mission Execution Result ---")
    print(f"Status: {res.status.value}")
    print(f"Completed Steps: {res.completed_steps_count} | Failed Steps: {res.failed_steps_count}")
    print(f"Verification Passed: {res.verification_passed}")
    print("Evidence Collected:")
    for ev in res.evidence:
        print(f"  - {ev}")

    print("\n>>> End-to-End Autonomous Mission Simulation COMPLETE <<<\n")


if __name__ == "__main__":
    main()
