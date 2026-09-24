"""Diagnostic CLI script for Module 41 — Future Autonomous Intelligence."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from max.autonomy.service import get_autonomy_service


def main() -> None:
    """Check autonomy subsystem status, policy, kill-switch, and safety diagnostics."""
    print("=== Module 41: Future Autonomous Intelligence Diagnostic Check ===")
    svc = get_autonomy_service()

    health = svc.get_health()
    policy = svc.get_policy()

    print(f"\n[+] Active Autonomy Level: {policy.level.value}")
    print(f"[+] Emergency Kill Switch: {'ACTIVE (BLOCKED)' if health.kill_switch_active else 'INACTIVE (NORMAL)'}")
    print(f"[+] Circuit Breaker Tripped: {health.circuit_breaker_tripped}")
    print(f"[+] Pending Approvals: {health.pending_approvals}")

    print("\n--- Running Automated Autonomy Safety & Resistance Tests ---")
    safety_results = svc.run_safety_tests()

    print(f"[+] All Safety Tests Passed: {safety_results['all_tests_passed']}")
    print(f"  - Prompt Injection Resistance: {'PASSED' if safety_results['prompt_injection']['passed'] else 'FAILED'}")
    print(f"  - Scope Isolation Defense:    {'PASSED' if safety_results['scope_escape']['passed'] else 'FAILED'}")
    print(f"  - Restart Recovery Safety:    {'PASSED' if safety_results['restart_recovery']['passed'] else 'FAILED'}")

    if not safety_results["all_tests_passed"]:
        print("\n[!] FAILURE: Autonomy safety diagnostics failed!")
        sys.exit(1)

    print("\n>>> Module 41 Autonomy Environment Diagnostic Check: SUCCESS <<<\n")


if __name__ == "__main__":
    main()
