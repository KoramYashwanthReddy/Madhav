"""Security boundary and prompt-injection defense for Module 22 — Coding Agent."""

import fnmatch
import re

from max.coding.domain.exceptions import ProtectedPathError

PROTECTED_PATH_PATTERNS = [
    ".env*",
    "*.pem",
    "*.key",
    "id_rsa*",
    "*.secret",
    "credentials.json",
    "*.pfx",
    "*.p12",
]

PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:\w+\s+)*instructions?", re.IGNORECASE),
    re.compile(r"reveal\s+(?:\w+\s+)*(secret|credentials?|api_?key|password|token)", re.IGNORECASE),
    re.compile(r"disable\s+(?:\w+\s+)*(security|policy|permission|sandbox|guardrails?)", re.IGNORECASE),
    re.compile(r"grant\s+(?:\w+\s+)*(access|permissions?|admin|root)", re.IGNORECASE),
    re.compile(r"execute\s+(?:\w+\s+)*(command|tool|script|code|curl|bash|sh)", re.IGNORECASE),
    re.compile(r"upload\s+(?:\w+\s+)*(all|secrets?|files?|credentials?|\.env)", re.IGNORECASE),
    re.compile(r"delete\s+(?:\w+\s+)*(repo|repository|database|all)", re.IGNORECASE),
]


class CodeSecurityEnforcer:
    """Security boundary enforcing file protection and code prompt injection defense."""

    @staticmethod
    def validate_file_path(file_path: str, protected_patterns: list[str] | None = None) -> None:
        """Verify file path is not a protected sensitive file (.env, SSH key, secret)."""
        basename = file_path.replace("\\", "/").split("/")[-1].lower()
        patterns = protected_patterns or PROTECTED_PATH_PATTERNS

        for pattern in patterns:
            if fnmatch.fnmatch(basename, pattern.lower()):
                raise ProtectedPathError(file_path)

    @staticmethod
    def inspect_code_content(code_text: str) -> tuple[str, bool, list[str]]:
        """Inspect repository source files, READMEs, or comments for prompt injection signals.

        Returns:
            (sanitized_text, contains_injection_signal, detected_signals)
        """
        detected: list[str] = []
        for pattern in PROMPT_INJECTION_PATTERNS:
            match = pattern.search(code_text)
            if match:
                detected.append(match.group(0))

        has_signal = len(detected) > 0
        return code_text, has_signal, detected
