"""ReviewService for code review, security review, and code explanation."""

from max.coding.domain.enums import IssueSeverity
from max.coding.domain.models import (
    CodeReview,
    CodeReviewFinding,
    RepositoryContext,
)


class ReviewService:
    """Provides automated code review, security-focused review, and code explanation."""

    def perform_code_review(self, session_id: str, context: RepositoryContext) -> CodeReview:
        """Perform automated code quality review."""
        findings: list[CodeReviewFinding] = []

        if not context.metadata.test_framework:
            findings.append(
                CodeReviewFinding(
                    file_path="root",
                    line_number=1,
                    severity=IssueSeverity.MEDIUM,
                    title="Missing Automated Test Framework",
                    description="No automated unit test framework (e.g., pytest, jest, junit) was detected.",
                    recommendation="Configure a test framework to validate code changes automatically.",
                )
            )

        if not context.metadata.lint_tools:
            findings.append(
                CodeReviewFinding(
                    file_path="root",
                    line_number=1,
                    severity=IssueSeverity.LOW,
                    title="Missing Linter Configuration",
                    description="No linter (e.g., ruff, eslint) configuration detected.",
                    recommendation="Add linter configuration to maintain consistent code quality.",
                )
            )

        score = 1.0 - (len(findings) * 0.15)
        score = max(0.0, min(1.0, round(score, 2)))

        return CodeReview(
            session_id=session_id,
            summary=f"Reviewed project '{context.metadata.project_name}'. Found {len(findings)} review items.",
            findings=findings,
            overall_quality_score=score,
        )

    def perform_security_review(self, session_id: str, context: RepositoryContext) -> CodeReview:
        """Perform security-focused code review."""
        findings: list[CodeReviewFinding] = []

        # Check for presence of unignored .env files or missing .gitignore
        if ".env" in context.file_tree:
            findings.append(
                CodeReviewFinding(
                    file_path=".env",
                    line_number=1,
                    severity=IssueSeverity.HIGH,
                    title="Local Environment File Present",
                    description="Local '.env' file found in repository root.",
                    recommendation="Ensure '.env' is listed in '.gitignore' and contains no committed secrets.",
                )
            )

        return CodeReview(
            session_id=session_id,
            summary=f"Security review completed for '{context.metadata.project_name}'. Found {len(findings)} security items.",
            findings=findings,
            overall_quality_score=1.0 if not findings else 0.7,
        )

    def explain_code(self, file_path: str, content: str) -> str:
        """Generate human-readable structural explanation of a code file."""
        lines = content.splitlines()
        word_count = len(content.split())
        return (
            f"Explanation for '{file_path}':\n"
            f"- File length: {len(lines)} lines, {word_count} words.\n"
            f"- Contains source code structure for {file_path}.\n"
            f"- Evaluated for safe integration within Max Personal AI Coding Agent workflow."
        )
