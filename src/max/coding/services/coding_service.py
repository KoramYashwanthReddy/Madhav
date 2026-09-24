"""Master CodingService orchestrating coding sessions and coding lifecycle."""

import logging
from datetime import datetime, timezone
from typing import Any

from max.coding.domain.enums import ChangeType, CodingStatus
from max.coding.domain.exceptions import CodingSessionNotFoundError
from max.coding.domain.models import (
    ChangeSet,
    CodePlan,
    CodingRequest,
    CodingResult,
    CodingSession,
    Patch,
    RepositoryContext,
)
from max.coding.repositories.repositories import (
    ChangeSetRepository,
    CodingAuditRepository,
    CodingSessionRepository,
)
from max.coding.services.audit_service import CodingAuditService
from max.coding.services.code_planner import CodePlanner
from max.coding.services.code_search import CodeSearchService
from max.coding.services.debugger_service import DebuggerService
from max.coding.services.patch_service import PatchService
from max.coding.services.repo_analyzer import RepositoryAnalyzer
from max.coding.services.review_service import ReviewService
from max.coding.services.validation_pipeline import ValidationPipeline

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CodingService:
    """Core facade managing Coding Agent sessions, patch sets, validation, and lifecycle state."""

    def __init__(
        self,
        session_repo: CodingSessionRepository | None = None,
        changeset_repo: ChangeSetRepository | None = None,
        audit_repo: CodingAuditRepository | None = None,
    ) -> None:
        self.session_repo = session_repo or CodingSessionRepository()
        self.changeset_repo = changeset_repo or ChangeSetRepository()
        self.audit_service = CodingAuditService(audit_repo)

        self.repo_analyzer = RepositoryAnalyzer()
        self.code_search = CodeSearchService()
        self.planner = CodePlanner()
        self.patch_svc = PatchService()
        self.validation = ValidationPipeline()
        self.debugger = DebuggerService()
        self.review_svc = ReviewService()

    async def create_session(self, request: CodingRequest) -> CodingSession:
        """Create a new Coding Session and analyze target repository."""
        session = CodingSession(request=request, status=CodingStatus.CREATED)
        self.session_repo.save(session)
        self.audit_service.log(session.id, "SESSION_CREATED", details={"repo_root": request.repo_path})

        # Step 1: ANALYZING
        session.status = CodingStatus.ANALYZING
        context = await self.repo_analyzer.analyze_repository(request.repo_path)
        session.context = context
        self.audit_service.log(session.id, "REPOSITORY_ANALYZED", details={"project_type": context.metadata.project_type.value})

        # Step 2: PLANNING
        session.status = CodingStatus.PLANNING
        plan = self.planner.create_plan(request)
        self.planner.validate_plan(plan)
        session.plan = plan
        self.audit_service.log(session.id, "PLAN_GENERATED", details={"steps_count": len(plan.steps)})

        session.status = CodingStatus.WAITING_FOR_APPROVAL
        session.updated_at = _utc_now()
        self.session_repo.save(session)
        return session

    def get_session(self, session_id: str) -> CodingSession:
        """Retrieve CodingSession by ID."""
        sess = self.session_repo.get(session_id)
        if not sess:
            raise CodingSessionNotFoundError(session_id)
        return sess

    async def create_patch_changeset(
        self,
        session_id: str,
        file_path: str,
        new_content: str,
        change_type: ChangeType = ChangeType.MODIFY_FILE,
    ) -> ChangeSet:
        """Generate a patch and ChangeSet for a session."""
        session = self.get_session(session_id)
        repo_root = session.request.repo_path

        orig_text = ""
        if change_type in (ChangeType.MODIFY_FILE, ChangeType.DELETE_FILE):
            try:
                orig_text = await self.code_search.read_file(repo_root, file_path)
            except Exception:
                orig_text = ""

        patch = self.patch_svc.create_patch(
            file_path=file_path,
            original_text=orig_text,
            new_text=new_content,
            change_type=change_type,
        )

        changeset = ChangeSet(session_id=session_id, patches=[patch])
        self.changeset_repo.save(changeset)
        session.active_changeset = changeset
        session.updated_at = _utc_now()
        self.session_repo.save(session)
        self.audit_service.log(session_id, "CHANGESET_CREATED", details={"changeset_id": changeset.id, "file": file_path})
        return changeset

    async def apply_changeset(self, session_id: str, changeset_id: str) -> ChangeSet:
        """Apply an active ChangeSet to the repository."""
        session = self.get_session(session_id)
        changeset = self.changeset_repo.get(changeset_id)
        if not changeset:
            raise CodingSessionNotFoundError(changeset_id)

        session.status = CodingStatus.MODIFYING
        await self.patch_svc.apply_changeset(session.request.repo_path, changeset)

        session.updated_at = _utc_now()
        self.session_repo.save(session)
        self.audit_service.log(session_id, "CHANGESET_APPLIED", details={"changeset_id": changeset_id})
        return changeset

    async def rollback_changeset(self, session_id: str, changeset_id: str) -> None:
        """Rollback an applied ChangeSet."""
        session = self.get_session(session_id)
        changeset = self.changeset_repo.get(changeset_id)
        if not changeset:
            raise CodingSessionNotFoundError(changeset_id)

        await self.patch_svc.rollback_changeset(session.request.repo_path, changeset)
        session.updated_at = _utc_now()
        self.session_repo.save(session)
        self.audit_service.log(session_id, "CHANGESET_ROLLED_BACK", details={"changeset_id": changeset_id})

    async def validate_session(self, session_id: str) -> CodingResult:
        """Run validation pipeline (compile/build, linter, typechecker, tests) for session."""
        session = self.get_session(session_id)
        repo_root = session.request.repo_path
        metadata = session.context.metadata if session.context else None

        session.status = CodingStatus.VALIDATING
        if metadata:
            build_run = await self.validation.run_build(repo_root, metadata)
            session.build_runs.append(build_run)

            lint_run = await self.validation.run_linter(repo_root, metadata)
            session.lint_runs.append(lint_run)

            type_run = await self.validation.run_typechecker(repo_root, metadata)
            session.typecheck_runs.append(type_run)

        session.status = CodingStatus.TESTING
        test_run = await self.validation.run_tests(repo_root, metadata) if metadata else None
        if test_run:
            session.test_runs.append(test_run)

        session.status = CodingStatus.REVIEWING
        review = self.review_svc.perform_code_review(session_id, session.context) if session.context else None

        session.status = CodingStatus.COMPLETED
        session.updated_at = _utc_now()
        self.session_repo.save(session)

        summary_text = (
            f"Coding session completed for objective '{session.request.objective.summary}'. "
            f"Build: {'Passed' if not session.build_runs or session.build_runs[-1].success else 'Failed'}, "
            f"Tests: {'Passed' if not session.test_runs or session.test_runs[-1].exit_code == 0 else 'Failed'}."
        )

        res = CodingResult(
            session_id=session.id,
            status=CodingStatus.COMPLETED,
            summary=summary_text,
            affected_files=session.plan.affected_files if session.plan else [],
            applied_changeset_id=session.active_changeset.id if session.active_changeset else None,
            test_summary=f"Ran {len(session.test_runs)} test execution(s)",
            review=review,
        )
        self.audit_service.log(session_id, "SESSION_COMPLETED")
        return res
