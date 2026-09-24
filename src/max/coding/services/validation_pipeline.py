from datetime import datetime, timezone

from max.coding.domain.enums import ProjectType
from max.coding.domain.models import BuildRun, LintRun, ProjectMetadata, TestRun, TypeCheckRun
from max.terminal.container import get_terminal_container
from max.terminal.domain.models import CommandRequest, CommandResult
from max.terminal.services.terminal_service import TerminalService


class ValidationPipeline:
    """Executes automated code validation tools via Terminal Agent."""

    def __init__(self, terminal_service: TerminalService | None = None) -> None:
        if terminal_service is not None:
            self.terminal_svc = terminal_service
        else:
            self.terminal_svc = get_terminal_container().terminal_service

    def _exec(self, exe: str, args: list[str], cwd: str) -> CommandResult:
        req = CommandRequest(
            command=exe,
            args=args,
            working_directory=cwd,
            owner_id="system",
        )
        return self.terminal_svc.execute_command(req)

    async def run_tests(
        self, repo_root: str, metadata: ProjectMetadata, target_test: str | None = None
    ) -> TestRun:
        """Run unit/integration tests for the repository."""
        exe = "python"
        args = ["-m", "pytest", "-x", "--tb=short"]

        if metadata.project_type == ProjectType.JAVA:
            exe = "mvn"
            args = ["test"]
        elif metadata.project_type in (ProjectType.JAVASCRIPT, ProjectType.TYPESCRIPT):
            exe = "npm"
            args = ["test"]
        elif metadata.project_type == ProjectType.RUST:
            exe = "cargo"
            args = ["test"]
        elif metadata.project_type == ProjectType.GO:
            exe = "go"
            args = ["test", "./..."]

        if target_test:
            args.append(target_test)

        cmd_str = f"{exe} {' '.join(args)}"
        start_t = datetime.now(timezone.utc)
        exec_res = self._exec(exe, args, repo_root)
        end_t = datetime.now(timezone.utc)
        duration = (end_t - start_t).total_seconds()

        exit_code = exec_res.exit_code if exec_res.exit_code is not None else 0
        passed = 1 if exit_code == 0 else 0
        failed = 0 if exit_code == 0 else 1
        output_str = f"STDOUT:\n{exec_res.stdout}\nSTDERR:\n{exec_res.stderr}"

        return TestRun(
            command=cmd_str,
            exit_code=exit_code,
            passed_count=passed,
            failed_count=failed,
            output=output_str,
            duration_seconds=duration,
        )

    async def run_build(self, repo_root: str, metadata: ProjectMetadata) -> BuildRun:
        """Run compilation or build check."""
        exe = "python"
        args = ["-m", "compileall", "src"]

        if metadata.project_type == ProjectType.JAVA:
            exe = "mvn"
            args = ["compile"]
        elif metadata.project_type in (ProjectType.JAVASCRIPT, ProjectType.TYPESCRIPT):
            exe = "npm"
            args = ["run", "build"]
        elif metadata.project_type == ProjectType.RUST:
            exe = "cargo"
            args = ["check"]
        elif metadata.project_type == ProjectType.GO:
            exe = "go"
            args = ["build", "./..."]

        cmd_str = f"{exe} {' '.join(args)}"
        start_t = datetime.now(timezone.utc)
        exec_res = self._exec(exe, args, repo_root)
        end_t = datetime.now(timezone.utc)
        duration = (end_t - start_t).total_seconds()

        exit_code = exec_res.exit_code if exec_res.exit_code is not None else 0
        output_str = f"STDOUT:\n{exec_res.stdout}\nSTDERR:\n{exec_res.stderr}"

        return BuildRun(
            command=cmd_str,
            exit_code=exit_code,
            success=(exit_code == 0),
            output=output_str,
            duration_seconds=duration,
        )

    async def run_linter(self, repo_root: str, metadata: ProjectMetadata) -> LintRun:
        """Run linter (e.g. ruff / eslint)."""
        exe = "python"
        args = ["-m", "ruff", "check", "."]

        if metadata.project_type in (ProjectType.JAVASCRIPT, ProjectType.TYPESCRIPT):
            exe = "npx"
            args = ["eslint", "."]

        cmd_str = f"{exe} {' '.join(args)}"
        exec_res = self._exec(exe, args, repo_root)
        exit_code = exec_res.exit_code if exec_res.exit_code is not None else 0
        output_str = f"STDOUT:\n{exec_res.stdout}\nSTDERR:\n{exec_res.stderr}"

        return LintRun(
            command=cmd_str,
            exit_code=exit_code,
            issues_found=0 if exit_code == 0 else 1,
            output=output_str,
        )

    async def run_typechecker(self, repo_root: str, metadata: ProjectMetadata) -> TypeCheckRun:
        """Run static type checker (e.g. mypy / tsc)."""
        exe = "python"
        args = ["-m", "mypy", "src"]

        if metadata.project_type == ProjectType.TYPESCRIPT:
            exe = "npx"
            args = ["tsc", "--noEmit"]

        cmd_str = f"{exe} {' '.join(args)}"
        exec_res = self._exec(exe, args, repo_root)
        exit_code = exec_res.exit_code if exec_res.exit_code is not None else 0
        output_str = f"STDOUT:\n{exec_res.stdout}\nSTDERR:\n{exec_res.stderr}"

        return TypeCheckRun(
            command=cmd_str,
            exit_code=exit_code,
            errors_found=0 if exit_code == 0 else 1,
            output=output_str,
        )
