"""DebuggerService for failure analysis, stack trace inspection, and bounded fix loops."""

import re

from max.coding.domain.enums import FailureCategory
from max.coding.domain.exceptions import MaxFixAttemptsExceededError
from max.coding.domain.models import DebugFinding, DebugSession


class DebuggerService:
    """Analyzes test and build failures, classifies error types, and manages bounded fix iteration loops."""

    def analyze_failure(self, output: str, exit_code: int = 1) -> DebugFinding:
        """Analyze failure output string and extract diagnostic findings."""
        category = FailureCategory.UNKNOWN
        suspected_file: str | None = None
        suspected_line: int | None = None
        err_msg = ""

        # Category classification heuristics
        if "AssertionError" in output or "FAILED" in output:
            category = FailureCategory.TEST_FAILURE
        elif "SyntaxError" in output or "IndentationError" in output:
            category = FailureCategory.CODE_ERROR
        elif "ModuleNotFoundError" in output or "ImportError" in output:
            category = FailureCategory.DEPENDENCY_ERROR
        elif "PermissionError" in output or "AccessDenied" in output:
            category = FailureCategory.PERMISSION_ERROR
        elif "Timeout" in output or "timed out" in output.lower():
            category = FailureCategory.TIMEOUT
        elif "build failed" in output.lower() or "compilation error" in output.lower():
            category = FailureCategory.BUILD_ERROR

        # Stack trace file & line extraction
        # Example pattern: File "path/to/file.py", line 42
        m_file = re.search(r'File "([^"]+)", line (\d+)', output)
        if m_file:
            suspected_file = m_file.group(1)
            suspected_line = int(m_file.group(2))

        # Extract last line of traceback as main error message
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        if lines:
            err_msg = lines[-1]

        return DebugFinding(
            failure_category=category,
            suspected_file=suspected_file,
            suspected_line=suspected_line,
            error_message=err_msg or f"Command failed with exit code {exit_code}.",
            suggested_fix=f"Review '{suspected_file or 'source code'}' and fix root cause of {category.value}.",
        )

    def start_debug_session(self, session_id: str, max_attempts: int = 3) -> DebugSession:
        """Initialize a new DebugSession record."""
        return DebugSession(session_id=session_id, attempt_count=0, max_attempts=max_attempts)

    def record_attempt(self, debug_session: DebugSession, finding: DebugFinding) -> None:
        """Record a fix attempt; raise MaxFixAttemptsExceededError if limit is reached."""
        debug_session.attempt_count += 1
        debug_session.findings.append(finding)

        if debug_session.attempt_count > debug_session.max_attempts:
            raise MaxFixAttemptsExceededError(debug_session.max_attempts)
