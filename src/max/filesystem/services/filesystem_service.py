"""Central FilesystemService coordinating path security, Module 15 authorization, audit tracing, and backend operations."""

import time
import uuid
from datetime import UTC, datetime
from typing import Any

from max.config.sections import FilesystemSettings
from max.filesystem.backends.base import FilesystemBackend
from max.filesystem.domain.action import (
    FileOperation,
    FileOperationFailure,
    FileOperationRequest,
    FileOperationResult,
)
from max.filesystem.domain.enums import (
    FileEncoding,
    FileFailureReason,
    FileOperationStatus,
    FileOperationType,
    FilesystemCapability,
)
from max.filesystem.domain.exceptions import (
    FilesystemError,
    InvalidFilesystemOperationError,
)
from max.filesystem.domain.models import FilesystemTraceEvent, PathReference, SearchFilter
from max.filesystem.repositories.operation_repository import FileOperationRepository
from max.filesystem.repositories.trace_repository import FilesystemTraceRepository
from max.filesystem.security.path_security import PathSecurityService
from max.filesystem.services.mutation_service import FilesystemMutationService
from max.filesystem.services.observation_service import FilesystemObservationService

# Integration with Module 15 Permission & Security
from max.security.domain import (
    PermissionAction,
    PermissionRequest,
    PermissionResource,
    PermissionSubject,
    PermissionSubjectType,
    ResourceSensitivity,
    RiskLevel,
)
from max.security.services.gate import PermissionGate


class FilesystemService:
    """Primary facade for all filesystem interactions in Max."""

    def __init__(
        self,
        settings: FilesystemSettings,
        path_security: PathSecurityService,
        backend: FilesystemBackend,
        operation_repo: FileOperationRepository,
        trace_repo: FilesystemTraceRepository,
        permission_gate: PermissionGate | None = None,
    ) -> None:
        self._settings = settings
        self._path_security = path_security
        self._backend = backend
        self._operation_repo = operation_repo
        self._trace_repo = trace_repo
        self._permission_gate = permission_gate

        self._observation_service = FilesystemObservationService(backend=backend)
        self._mutation_service = FilesystemMutationService(backend=backend)

    @property
    def settings(self) -> FilesystemSettings:
        """Get filesystem settings."""
        return self._settings

    @property
    def backend(self) -> FilesystemBackend:
        """Get underlying filesystem backend."""
        return self._backend

    def get_status(self) -> dict[str, Any]:
        """Return operational status and capabilities of the Filesystem Agent."""
        return {
            "enabled": self._settings.enabled,
            "dry_run": self._settings.dry_run,
            "backend_type": type(self._backend).__name__,
            "allowed_roots": [str(r) for r in self._path_security.allowed_roots],
            "read_only_roots": [str(r) for r in self._path_security.read_only_roots],
            "blocked_roots": [str(r) for r in self._path_security.blocked_roots],
            "capabilities": [c.value for c in FilesystemCapability],
            "permission_gate_active": self._permission_gate is not None,
        }

    def execute_operation(
        self, request: FileOperationRequest
    ) -> FileOperationResult:
        """Execute a filesystem operation request with full validation, authorization, and auditing."""
        start_time = time.monotonic()
        operation = FileOperation(request=request, status=FileOperationStatus.CREATED)
        self._operation_repo.save(operation)

        # 0. Subsystem Enabled Check
        if not self._settings.enabled:
            return self._fail_operation(
                operation=operation,
                reason=FileFailureReason.OS_ERROR,
                message="Filesystem Agent is disabled in configuration.",
                start_time=start_time,
            )

        # 1. Path Normalization & Security Validation
        operation.status = FileOperationStatus.VALIDATING
        self._operation_repo.save(operation)

        try:
            target_ref, dest_ref = self._validate_and_normalize_paths(request)
        except FilesystemError as exc:
            self._record_trace(
                operation_id=request.operation_id,
                event_type="PATH_SECURITY_VIOLATION",
                details={"error": str(exc)},
            )
            return self._fail_operation(
                operation=operation,
                reason=FileFailureReason.SANDBOX_VIOLATION,
                message=str(exc),
                start_time=start_time,
            )

        # 2. Module 15 Permission & Security Check
        operation.status = FileOperationStatus.AUTHORIZED
        self._operation_repo.save(operation)

        if self._permission_gate is not None:
            perm_decision, auth_token = self._authorize_operation(request, target_ref, dest_ref)
            if perm_decision is None or perm_decision.status.value != "ALLOWED":
                message = perm_decision.message if perm_decision else "Permission denied by Module 15."
                self._record_trace(
                    operation_id=request.operation_id,
                    event_type="PERMISSION_BLOCKED",
                    details={"message": message},
                )
                return self._fail_operation(
                    operation=operation,
                    reason=FileFailureReason.PERMISSION_DENIED,
                    message=message,
                    start_time=start_time,
                )

        # 3. Dry-Run Check
        is_dry_run = self._settings.dry_run or request.parameters.get("dry_run", False)
        if is_dry_run:
            operation.status = FileOperationStatus.SIMULATED
            duration = time.monotonic() - start_time
            result = FileOperationResult(
                operation_id=request.operation_id,
                operation_type=request.operation_type,
                status=FileOperationStatus.SIMULATED,
                source=request.source,
                destination=request.destination,
                duration=duration,
                observed_state={
                    "simulated": True,
                    "message": f"Simulated operation '{request.operation_type.value}' successfully.",
                },
            )
            operation.result = result
            operation.updated_at = datetime.now(UTC)
            self._operation_repo.save(operation)
            self._record_trace(
                operation_id=request.operation_id,
                event_type="FILE_OPERATION_SIMULATED",
            )
            return result

        # 4. Perform Backend Execution
        operation.status = FileOperationStatus.RUNNING
        self._operation_repo.save(operation)

        self._record_trace(
            operation_id=request.operation_id,
            event_type="FILE_OPERATION_STARTED",
        )

        try:
            res_data = self._dispatch_backend(request, target_ref, dest_ref)
            duration = time.monotonic() - start_time
            result = FileOperationResult(
                operation_id=request.operation_id,
                operation_type=request.operation_type,
                status=FileOperationStatus.COMPLETED,
                source=request.source,
                destination=request.destination,
                duration=duration,
                observed_state=res_data,
            )
            operation.status = FileOperationStatus.COMPLETED
            operation.result = result
            operation.updated_at = datetime.now(UTC)
            self._operation_repo.save(operation)

            self._record_trace(
                operation_id=request.operation_id,
                event_type="FILE_OPERATION_COMPLETED",
            )
            return result

        except FilesystemError as exc:
            return self._fail_operation(
                operation=operation,
                reason=FileFailureReason.OS_ERROR,
                message=str(exc),
                start_time=start_time,
            )
        except Exception as exc:
            return self._fail_operation(
                operation=operation,
                reason=FileFailureReason.INTERNAL_ERROR,
                message=f"Unexpected internal error: {exc}",
                start_time=start_time,
            )

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _validate_and_normalize_paths(
        self, request: FileOperationRequest
    ) -> tuple[PathReference, PathReference | None]:
        """Validate source and optional destination paths against path security rules."""
        is_write = request.operation_type in {
            FileOperationType.WRITE_FILE,
            FileOperationType.APPEND_FILE,
            FileOperationType.CREATE_FILE,
            FileOperationType.CREATE_DIRECTORY,
            FileOperationType.DELETE_FILE,
            FileOperationType.DELETE_DIRECTORY,
            FileOperationType.MOVE,
            FileOperationType.RENAME,
            FileOperationType.COPY_FILE,
            FileOperationType.COPY_DIRECTORY,
        }

        # Check source path
        target_ref = self._path_security.verify_path_access(
            raw_path=request.source, is_write=is_write
        )

        dest_ref: PathReference | None = None
        if request.destination:
            dest_ref = self._path_security.verify_path_access(
                raw_path=request.destination, is_write=True
            )

        # For COPY, MOVE, RENAME dual-boundary check
        if request.operation_type in {
            FileOperationType.COPY_FILE,
            FileOperationType.COPY_DIRECTORY,
            FileOperationType.MOVE,
            FileOperationType.RENAME,
        }:
            if dest_ref is None or request.destination is None:
                raise InvalidFilesystemOperationError(
                    f"Destination path is required for {request.operation_type.value}"
                )
            self._path_security.verify_dual_path_access(
                source_raw=request.source,
                dest_raw=request.destination,
                is_move_or_rename=(
                    request.operation_type in {FileOperationType.MOVE, FileOperationType.RENAME}
                ),
            )

        return target_ref, dest_ref

    def _authorize_operation(
        self,
        request: FileOperationRequest,
        target_ref: PathReference,
        dest_ref: PathReference | None,
    ) -> tuple[Any, Any]:
        """Construct PermissionRequest and submit to Module 15 PermissionGate."""
        action_map = {
            FileOperationType.EXISTS: PermissionAction.READ,
            FileOperationType.STAT: PermissionAction.READ,
            FileOperationType.LIST_DIRECTORY: PermissionAction.READ,
            FileOperationType.READ_FILE: PermissionAction.READ,
            FileOperationType.SEARCH: PermissionAction.READ,
            FileOperationType.HASH: PermissionAction.READ,
            FileOperationType.COMPARE: PermissionAction.READ,
            FileOperationType.CREATE_FILE: PermissionAction.WRITE,
            FileOperationType.CREATE_DIRECTORY: PermissionAction.WRITE,
            FileOperationType.WRITE_FILE: PermissionAction.WRITE,
            FileOperationType.APPEND_FILE: PermissionAction.WRITE,
            FileOperationType.COPY_FILE: PermissionAction.WRITE,
            FileOperationType.COPY_DIRECTORY: PermissionAction.WRITE,
            FileOperationType.MOVE: PermissionAction.MODIFY,
            FileOperationType.RENAME: PermissionAction.MODIFY,
            FileOperationType.DELETE_FILE: PermissionAction.DELETE,
            FileOperationType.DELETE_DIRECTORY: PermissionAction.DELETE,
        }

        risk_map = {
            FileOperationType.EXISTS: RiskLevel.LOW,
            FileOperationType.STAT: RiskLevel.LOW,
            FileOperationType.LIST_DIRECTORY: RiskLevel.LOW,
            FileOperationType.READ_FILE: RiskLevel.MEDIUM,
            FileOperationType.SEARCH: RiskLevel.MEDIUM,
            FileOperationType.HASH: RiskLevel.LOW,
            FileOperationType.COMPARE: RiskLevel.LOW,
            FileOperationType.CREATE_FILE: RiskLevel.MEDIUM,
            FileOperationType.CREATE_DIRECTORY: RiskLevel.MEDIUM,
            FileOperationType.WRITE_FILE: RiskLevel.HIGH,
            FileOperationType.APPEND_FILE: RiskLevel.HIGH,
            FileOperationType.COPY_FILE: RiskLevel.MEDIUM,
            FileOperationType.COPY_DIRECTORY: RiskLevel.MEDIUM,
            FileOperationType.MOVE: RiskLevel.HIGH,
            FileOperationType.RENAME: RiskLevel.HIGH,
            FileOperationType.DELETE_FILE: RiskLevel.HIGH,
            FileOperationType.DELETE_DIRECTORY: RiskLevel.CRITICAL,
        }

        perm_action = action_map.get(request.operation_type, PermissionAction.READ)
        risk_level = risk_map.get(request.operation_type, RiskLevel.MEDIUM)

        is_sensitive = self._path_security.is_sensitive_path(target_ref.resolved_path)
        sensitivity = (
            ResourceSensitivity.SENSITIVE if is_sensitive else ResourceSensitivity.NORMAL
        )

        perm_request = PermissionRequest(
            request_id=f"perm_{uuid.uuid4().hex[:12]}",
            owner_id=request.owner_id,
            subject=PermissionSubject(
                subject_id=request.agent_id or "agent_fs",
                subject_type=PermissionSubjectType.AGENT,
            ),
            resource=PermissionResource(
                resource_type="FILE",
                resource_id=target_ref.resolved_path,
                owner_id=request.owner_id,
                sensitivity=sensitivity,
                attributes={"path": target_ref.resolved_path},
            ),
            action=perm_action,
            risk_level=risk_level,
            tool_reference=f"filesystem.{request.operation_type.value.lower()}",
            arguments={"parameters": request.parameters},
        )

        assert self._permission_gate is not None
        return self._permission_gate.check_and_authorize(perm_request)

    def _dispatch_backend(
        self,
        request: FileOperationRequest,
        target_ref: PathReference,
        dest_ref: PathReference | None,
    ) -> dict[str, Any]:
        """Dispatch validated operation request to underlying observation or mutation service."""
        op_type = request.operation_type
        params = request.parameters

        if op_type == FileOperationType.EXISTS:
            res_exists = self._observation_service.exists(target_ref)
            return {"exists": res_exists}

        elif op_type == FileOperationType.STAT:
            stat_meta = self._observation_service.stat(target_ref)
            return stat_meta.model_dump(mode="json")

        elif op_type == FileOperationType.LIST_DIRECTORY:
            listing = self._observation_service.list_directory(target_ref)
            return listing.model_dump(mode="json")

        elif op_type == FileOperationType.READ_FILE:
            encoding_str = params.get("encoding", "utf-8")
            enc_enum = FileEncoding(encoding_str) if isinstance(encoding_str, str) else encoding_str
            max_bytes = params.get("max_bytes", self._settings.max_read_bytes)
            offset = params.get("offset", 0)
            read_res = self._observation_service.read_file(
                path=target_ref, encoding=enc_enum, max_bytes=max_bytes, offset=offset
            )
            return read_res.model_dump(mode="json")

        elif op_type == FileOperationType.WRITE_FILE:
            content = params.get("content", "")
            encoding_str = params.get("encoding", "utf-8")
            enc_enum = FileEncoding(encoding_str) if isinstance(encoding_str, str) else encoding_str
            overwrite = params.get("overwrite", True)
            create_parents = params.get("create_parents", True)
            write_res = self._mutation_service.write_file(
                path=target_ref,
                content=content,
                encoding=enc_enum,
                overwrite=overwrite,
                create_parents=create_parents,
            )
            return write_res.model_dump(mode="json")

        elif op_type == FileOperationType.APPEND_FILE:
            content = params.get("content", "")
            encoding_str = params.get("encoding", "utf-8")
            enc_enum = FileEncoding(encoding_str) if isinstance(encoding_str, str) else encoding_str
            append_res = self._mutation_service.append_file(
                path=target_ref, content=content, encoding=enc_enum
            )
            return append_res.model_dump(mode="json")

        elif op_type == FileOperationType.CREATE_FILE:
            created_meta = self._mutation_service.create_file(path=target_ref)
            return created_meta.model_dump(mode="json")

        elif op_type == FileOperationType.CREATE_DIRECTORY:
            parents = params.get("parents", True)
            mkdir_meta = self._mutation_service.create_directory(path=target_ref, parents=parents)
            return mkdir_meta.model_dump(mode="json")

        elif op_type == FileOperationType.COPY_FILE:
            assert dest_ref is not None
            overwrite = params.get("overwrite", False)
            copy_meta = self._mutation_service.copy_file(
                source=target_ref, destination=dest_ref, overwrite=overwrite
            )
            return copy_meta.model_dump(mode="json")

        elif op_type == FileOperationType.COPY_DIRECTORY:
            assert dest_ref is not None
            overwrite = params.get("overwrite", False)
            copydir_meta = self._mutation_service.copy_directory(
                source=target_ref, destination=dest_ref, overwrite=overwrite
            )
            return copydir_meta.model_dump(mode="json")

        elif op_type == FileOperationType.MOVE:
            assert dest_ref is not None
            overwrite = params.get("overwrite", False)
            move_meta = self._mutation_service.move(
                source=target_ref, destination=dest_ref, overwrite=overwrite
            )
            return move_meta.model_dump(mode="json")

        elif op_type == FileOperationType.RENAME:
            assert dest_ref is not None
            rename_meta = self._mutation_service.rename(
                source=target_ref, new_name=dest_ref.resolved_path
            )
            return rename_meta.model_dump(mode="json")

        elif op_type == FileOperationType.DELETE_FILE:
            deleted = self._mutation_service.delete_file(target_ref)
            return {"deleted": deleted}

        elif op_type == FileOperationType.DELETE_DIRECTORY:
            recursive = params.get("recursive", False)
            deleted = self._mutation_service.delete_directory(target_ref, recursive=recursive)
            return {"deleted": deleted}

        elif op_type == FileOperationType.SEARCH:
            s_filter = SearchFilter(
                query=params.get("pattern", "*"),
                max_depth=params.get("max_depth", self._settings.max_search_depth),
                max_results=params.get("max_results", self._settings.max_search_results),
            )
            s_res = self._observation_service.search(root_path=target_ref, search_filter=s_filter)
            return s_res.model_dump(mode="json")

        elif op_type == FileOperationType.HASH:
            algorithm = params.get("algorithm", "SHA-256")
            h_res = self._observation_service.hash_file(path=target_ref, algorithm=algorithm)
            return h_res.model_dump(mode="json")

        elif op_type == FileOperationType.COMPARE:
            assert dest_ref is not None
            c_res = self._observation_service.compare_files(path1=target_ref, path2=dest_ref)
            return c_res.model_dump(mode="json")

        else:
            raise InvalidFilesystemOperationError(f"Unsupported operation type: {op_type}")

    def _fail_operation(
        self,
        operation: FileOperation,
        reason: FileFailureReason,
        message: str,
        start_time: float,
    ) -> FileOperationResult:
        """Mark operation failed and record failure state & audit trace."""
        duration = time.monotonic() - start_time
        failure = FileOperationFailure(
            operation_id=operation.request.operation_id,
            operation_type=operation.request.operation_type,
            reason=reason,
            message=message,
            timestamp=datetime.now(UTC),
        )
        result = FileOperationResult(
            operation_id=operation.request.operation_id,
            operation_type=operation.request.operation_type,
            status=FileOperationStatus.FAILED,
            source=operation.request.source,
            destination=operation.request.destination,
            duration=duration,
            observed_state={"error_reason": reason.value, "error_message": message},
        )

        operation.status = FileOperationStatus.FAILED
        operation.failure = failure
        operation.result = result
        operation.updated_at = datetime.now(UTC)
        self._operation_repo.save(operation)

        self._record_trace(
            operation_id=operation.request.operation_id,
            event_type="FILE_OPERATION_FAILED",
            details={"reason": reason.value, "message": message},
        )
        return result

    def _record_trace(
        self,
        operation_id: str,
        event_type: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record trace audit event."""
        trace = FilesystemTraceEvent(
            event_id=f"fevt_{uuid.uuid4().hex[:12]}",
            operation_id=operation_id,
            event_type=event_type,
            details=details or {},
        )
        self._trace_repo.add_event(trace)
