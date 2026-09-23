"""Tool Invocation Service orchestrating full invocation pipelines and boundaries."""

import logging
import time
from datetime import datetime

from max.config.sections import ToolRegistrySettings
from max.tools.domain.enums import (
    ToolEventType,
    ToolFailureCategory,
    ToolInvocationStatus,
)
from max.tools.domain.exceptions import (
    ToolError,
    ToolExecutionBoundaryError,
    ToolInvocationNotFoundError,
    ToolInvocationStateError,
    ToolPermissionRequiredError,
)
from max.tools.domain.invocation import (
    ToolInvocation,
    ToolInvocationContext,
    ToolInvocationFailure,
    ToolInvocationRequest,
    ToolInvocationResult,
)
from max.tools.providers.boundaries import DevPermissionGateway, DevToolExecutionGateway
from max.tools.repositories.invocation_repository import (
    BaseToolInvocationRepository,
    MemoryToolInvocationRepository,
)
from max.tools.repositories.tool_repository import BaseToolRepository, MemoryToolRepository
from max.tools.services.resolver import ToolResolver
from max.tools.services.trace_service import ToolTraceService
from max.tools.validators.argument_validator import ToolArgumentValidator
from max.tools.validators.output_validator import ToolOutputValidator

logger = logging.getLogger(__name__)


class ToolInvocationService:
    """Service managing tool invocation lifecycles, validations, permissions, and boundaries."""

    def __init__(
        self,
        invocation_repository: BaseToolInvocationRepository | None = None,
        tool_repository: BaseToolRepository | None = None,
        resolver: ToolResolver | None = None,
        trace_service: ToolTraceService | None = None,
        permission_gateway: DevPermissionGateway | None = None,
        execution_gateway: DevToolExecutionGateway | None = None,
        settings: ToolRegistrySettings | None = None,
    ) -> None:
        self.invocation_repo = invocation_repository or MemoryToolInvocationRepository()
        self.tool_repo = tool_repository or MemoryToolRepository()
        self.trace_service = trace_service or ToolTraceService()
        self.resolver = resolver or ToolResolver(
            tool_repository=self.tool_repo, trace_service=self.trace_service
        )
        self.permission_gateway = permission_gateway or DevPermissionGateway()
        self.execution_gateway = execution_gateway or DevToolExecutionGateway()
        self.settings = settings or ToolRegistrySettings()

    @property
    def repository(self) -> BaseToolInvocationRepository:
        return self.invocation_repo

    def invoke_tool(self, request: ToolInvocationRequest) -> ToolInvocationResult:
        """Execute complete tool invocation pipeline."""
        start_time = time.time()

        # Check idempotency key if provided
        if request.client_request_id:
            existing = self.invocation_repo.get_by_client_request_id(request.client_request_id)
            if existing and existing.result:
                return existing.result

        # 1. Resolve tool
        try:
            resolved_tool = self.resolver.resolve_tool(
                tool_identifier=request.tool_name, version=request.tool_version
            )
        except ToolError as e:
            # Handle resolution failure
            return self._handle_early_failure(
                request=request,
                error_message=str(e),
                category=ToolFailureCategory.TOOL_NOT_FOUND,
                start_time=start_time,
            )

        tool = resolved_tool.tool

        # Construct context pointers
        context = ToolInvocationContext(
            plan_id=request.plan_id,
            plan_step_id=request.plan_step_id,
            task_id=request.task_id,
            agent_id=request.agent_id,
            run_id=request.run_id,
            conversation_id=request.conversation_id,
            owner_id=request.owner_id,
            metadata=request.metadata,
        )

        # Create invocation entity
        invocation = ToolInvocation(
            tool_id=tool.id,
            tool_version=tool.version,
            arguments=request.arguments,
            execution_mode=request.execution_mode,
            status=ToolInvocationStatus.CREATED,
            client_request_id=request.client_request_id,
            context=context,
            started_at=datetime.utcnow(),
            metadata=request.metadata,
        )
        invocation = self.invocation_repo.save(invocation)

        self.trace_service.record_event(
            event_type=ToolEventType.INVOCATION_CREATED,
            tool_id=tool.id,
            invocation_id=invocation.invocation_id,
            agent_id=request.agent_id,
            run_id=request.run_id,
            task_id=request.task_id,
            summary=f"Invocation '{invocation.invocation_id}' created for tool '{tool.name}'",
        )

        # 2. Validate Input Arguments
        try:
            invocation = self._update_invocation_status(invocation, ToolInvocationStatus.VALIDATING)
            ToolArgumentValidator.validate(tool.id, request.arguments, tool.input_schema)
            self.trace_service.record_event(
                event_type=ToolEventType.ARGUMENTS_VALIDATED,
                tool_id=tool.id,
                invocation_id=invocation.invocation_id,
                summary=f"Input arguments validated successfully for '{tool.name}'",
            )
        except ToolError as e:
            return self._fail_invocation(
                invocation=invocation,
                tool_id=tool.id,
                message=str(e),
                category=ToolFailureCategory.VALIDATION_ERROR,
                start_time=start_time,
            )

        # 3. Pass Permission Boundary (Module 15 extension point)
        try:
            invocation = self._update_invocation_status(
                invocation, ToolInvocationStatus.WAITING_PERMISSION
            )
            self.trace_service.record_event(
                event_type=ToolEventType.PERMISSION_REQUESTED,
                tool_id=tool.id,
                invocation_id=invocation.invocation_id,
                summary=f"Permission boundary check requested for '{tool.name}'",
            )

            perm_check = self.permission_gateway.check_permission(tool, invocation)

            self.trace_service.record_event(
                event_type=ToolEventType.PERMISSION_GRANTED,
                tool_id=tool.id,
                invocation_id=invocation.invocation_id,
                summary=f"Permission check passed for '{tool.name}' ({perm_check.get('boundary')})",
            )
        except ToolPermissionRequiredError as e:
            self.trace_service.record_event(
                event_type=ToolEventType.PERMISSION_DENIED,
                tool_id=tool.id,
                invocation_id=invocation.invocation_id,
                summary=f"Permission required for '{tool.name}': {str(e)}",
            )
            return self._fail_invocation(
                invocation=invocation,
                tool_id=tool.id,
                message=str(e),
                category=ToolFailureCategory.PERMISSION_REQUIRED,
                start_time=start_time,
                target_status=ToolInvocationStatus.REJECTED,
            )

        # 4. Pass Execution Boundary (Module 16+ execution gateway)
        try:
            invocation = self._update_invocation_status(invocation, ToolInvocationStatus.RUNNING)
            self.trace_service.record_event(
                event_type=ToolEventType.EXECUTION_STARTED,
                tool_id=tool.id,
                invocation_id=invocation.invocation_id,
                summary=f"Tool execution started for '{tool.name}'",
            )

            output_data = self.execution_gateway.execute(tool, invocation)

            self.trace_service.record_event(
                event_type=ToolEventType.EXECUTION_COMPLETED,
                tool_id=tool.id,
                invocation_id=invocation.invocation_id,
                summary=f"Tool execution completed for '{tool.name}'",
            )
        except ToolExecutionBoundaryError as e:
            return self._fail_invocation(
                invocation=invocation,
                tool_id=tool.id,
                message=str(e),
                category=ToolFailureCategory.EXECUTION_ERROR,
                start_time=start_time,
            )
        except ToolError as e:
            return self._fail_invocation(
                invocation=invocation,
                tool_id=tool.id,
                message=str(e),
                category=ToolFailureCategory.EXECUTION_ERROR,
                start_time=start_time,
            )

        # 5. Validate Output Schema
        try:
            ToolOutputValidator.validate(tool.id, output_data, tool.output_schema)
            self.trace_service.record_event(
                event_type=ToolEventType.OUTPUT_VALIDATED,
                tool_id=tool.id,
                invocation_id=invocation.invocation_id,
                summary=f"Output payload validated successfully for '{tool.name}'",
            )
        except ToolError as e:
            return self._fail_invocation(
                invocation=invocation,
                tool_id=tool.id,
                message=str(e),
                category=ToolFailureCategory.INVALID_OUTPUT,
                start_time=start_time,
            )

        # 6. Complete Invocation
        duration = round(time.time() - start_time, 4)
        completed_at = datetime.utcnow()

        result = ToolInvocationResult(
            invocation_id=invocation.invocation_id,
            tool_id=tool.id,
            status=ToolInvocationStatus.COMPLETED,
            output=output_data,
            duration_seconds=duration,
            created_at=invocation.created_at,
            completed_at=completed_at,
        )

        inv_dict = invocation.model_dump()
        inv_dict["status"] = ToolInvocationStatus.COMPLETED
        inv_dict["completed_at"] = completed_at
        inv_dict["result"] = result
        inv_dict["updated_at"] = completed_at

        saved_inv = self.invocation_repo.save(ToolInvocation(**inv_dict))

        self.trace_service.record_event(
            event_type=ToolEventType.INVOCATION_COMPLETED,
            tool_id=tool.id,
            invocation_id=saved_inv.invocation_id,
            summary=f"Invocation '{saved_inv.invocation_id}' completed successfully in {duration}s",
        )

        logger.info(
            "Tool invocation completed",
            extra={
                "invocation_id": saved_inv.invocation_id,
                "tool_id": tool.id,
                "duration": duration,
            },
        )
        return result

    def get_invocation(self, invocation_id: str) -> ToolInvocation:
        """Retrieve tool invocation by ID."""
        inv = self.invocation_repo.get_by_id(invocation_id)
        if not inv:
            raise ToolInvocationNotFoundError(invocation_id)
        return inv

    def cancel_invocation(
        self, invocation_id: str, reason: str = "Cancelled by user"
    ) -> ToolInvocation:
        """Cancel an active or pending invocation."""
        inv = self.get_invocation(invocation_id)
        if inv.status in (
            ToolInvocationStatus.COMPLETED,
            ToolInvocationStatus.FAILED,
            ToolInvocationStatus.CANCELLED,
        ):
            raise ToolInvocationStateError(inv.status.value, ToolInvocationStatus.CANCELLED.value)

        completed_at = datetime.utcnow()
        failure = ToolInvocationFailure(
            error_code="INVOCATION_CANCELLED",
            message=reason,
            category=ToolFailureCategory.CANCELLED,
            occurred_at=completed_at,
            invocation_id=invocation_id,
        )

        inv_dict = inv.model_dump()
        inv_dict["status"] = ToolInvocationStatus.CANCELLED
        inv_dict["completed_at"] = completed_at
        inv_dict["failure"] = failure
        inv_dict["updated_at"] = completed_at

        saved = self.invocation_repo.save(ToolInvocation(**inv_dict))

        self.trace_service.record_event(
            event_type=ToolEventType.INVOCATION_CANCELLED,
            tool_id=inv.tool_id,
            invocation_id=invocation_id,
            summary=f"Invocation '{invocation_id}' cancelled: {reason}",
        )
        return saved

    def list_invocations(
        self,
        tool_id: str | None = None,
        agent_id: str | None = None,
        run_id: str | None = None,
        task_id: str | None = None,
        status: ToolInvocationStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ToolInvocation], int]:
        """List tool invocations with filters and pagination."""
        effective_limit = min(limit, self.settings.max_page_size)
        return self.invocation_repo.list_invocations(
            tool_id=tool_id,
            agent_id=agent_id,
            run_id=run_id,
            task_id=task_id,
            status=status,
            limit=effective_limit,
            offset=offset,
        )

    def _update_invocation_status(
        self, invocation: ToolInvocation, target_status: ToolInvocationStatus
    ) -> ToolInvocation:
        inv_dict = invocation.model_dump()
        inv_dict["status"] = target_status
        inv_dict["updated_at"] = datetime.utcnow()
        return self.invocation_repo.save(ToolInvocation(**inv_dict))

    def _fail_invocation(
        self,
        invocation: ToolInvocation,
        tool_id: str,
        message: str,
        category: ToolFailureCategory,
        start_time: float,
        target_status: ToolInvocationStatus = ToolInvocationStatus.FAILED,
    ) -> ToolInvocationResult:
        completed_at = datetime.utcnow()
        duration = round(time.time() - start_time, 4)

        failure = ToolInvocationFailure(
            error_code=f"TOOL_{category.value}",
            message=message,
            category=category,
            occurred_at=completed_at,
            invocation_id=invocation.invocation_id,
        )

        result = ToolInvocationResult(
            invocation_id=invocation.invocation_id,
            tool_id=tool_id,
            status=target_status,
            output={},
            duration_seconds=duration,
            created_at=invocation.created_at,
            completed_at=completed_at,
        )

        inv_dict = invocation.model_dump()
        inv_dict["status"] = target_status
        inv_dict["completed_at"] = completed_at
        inv_dict["failure"] = failure
        inv_dict["result"] = result
        inv_dict["updated_at"] = completed_at

        saved = self.invocation_repo.save(ToolInvocation(**inv_dict))

        self.trace_service.record_event(
            event_type=ToolEventType.EXECUTION_FAILED,
            tool_id=tool_id,
            invocation_id=saved.invocation_id,
            summary=f"Invocation '{saved.invocation_id}' failed ({category.value}): {message}",
        )
        return result

    def _handle_early_failure(
        self,
        request: ToolInvocationRequest,
        error_message: str,
        category: ToolFailureCategory,
        start_time: float,
    ) -> ToolInvocationResult:
        completed_at = datetime.utcnow()
        duration = round(time.time() - start_time, 4)

        dummy_inv = ToolInvocation(
            tool_id=request.tool_name,
            arguments=request.arguments,
            execution_mode=request.execution_mode,
            status=ToolInvocationStatus.FAILED,
            client_request_id=request.client_request_id,
            completed_at=completed_at,
        )

        failure = ToolInvocationFailure(
            error_code=f"TOOL_{category.value}",
            message=error_message,
            category=category,
            occurred_at=completed_at,
            invocation_id=dummy_inv.invocation_id,
        )

        result = ToolInvocationResult(
            invocation_id=dummy_inv.invocation_id,
            tool_id=request.tool_name,
            status=ToolInvocationStatus.FAILED,
            output={},
            duration_seconds=duration,
            created_at=dummy_inv.created_at,
            completed_at=completed_at,
        )

        inv_dict = dummy_inv.model_dump()
        inv_dict["failure"] = failure
        inv_dict["result"] = result
        saved = self.invocation_repo.save(ToolInvocation(**inv_dict))

        self.trace_service.record_event(
            event_type=ToolEventType.EXECUTION_FAILED,
            tool_id=request.tool_name,
            invocation_id=saved.invocation_id,
            agent_id=request.agent_id,
            run_id=request.run_id,
            task_id=request.task_id,
            summary=f"Early invocation failure ({category.value}): {error_message}",
        )
        return result
