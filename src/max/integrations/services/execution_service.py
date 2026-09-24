"""Integration Action Execution Engine for Module 29."""

import logging
import threading
import time
from datetime import UTC, datetime

from max.integrations.adapters.adapters import Module15SecurityAdapter, Module27NotificationAdapter
from max.integrations.domain.enums import ConnectionStatus, ErrorCode
from max.integrations.domain.exceptions import (
    ActionExecutionError,
    PermissionDeniedIntegrationError,
    RateLimitExceededError,
)
from max.integrations.domain.models import (
    IntegrationAuditEvent,
    IntegrationRequest,
    IntegrationResponse,
)
from max.integrations.repositories.repositories import (
    BaseIntegrationAuditRepository,
    MemoryIntegrationAuditRepository,
)
from max.integrations.secrets.secret_store import SecretStore
from max.integrations.services.connection_service import ConnectionService
from max.integrations.services.registry import IntegrationRegistry

logger = logging.getLogger(__name__)


class RateLimiter:
    """Thread-safe sliding-window rate limiter per connection."""

    def __init__(self, max_requests_per_minute: int = 60) -> None:
        self.max_requests = max_requests_per_minute
        self._timestamps: dict[str, list[float]] = {}
        self._lock = threading.RLock()

    def check_and_record(self, key: str) -> bool:
        now = time.time()
        cutoff = now - 60.0
        with self._lock:
            ts_list = self._timestamps.get(key, [])
            ts_list = [t for t in ts_list if t > cutoff]
            if len(ts_list) >= self.max_requests:
                self._timestamps[key] = ts_list
                return False
            ts_list.append(now)
            self._timestamps[key] = ts_list
            return True


class IntegrationExecutionService:
    """Executes external integration actions with security, rate limiting, idempotency, retries, and audit logging."""

    def __init__(
        self,
        registry: IntegrationRegistry,
        connection_service: ConnectionService,
        secret_store: SecretStore,
        audit_repo: BaseIntegrationAuditRepository | None = None,
        security_adapter: Module15SecurityAdapter | None = None,
        notification_adapter: Module27NotificationAdapter | None = None,
        max_rate_per_minute: int = 60,
    ) -> None:
        self._registry = registry
        self._connection_service = connection_service
        self._secret_store = secret_store
        self._audit_repo = audit_repo or MemoryIntegrationAuditRepository()
        self._security_adapter = security_adapter or Module15SecurityAdapter()
        self._notification_adapter = notification_adapter or Module27NotificationAdapter()
        self._rate_limiter = RateLimiter(max_requests_per_minute=max_rate_per_minute)
        self._idempotency_cache: dict[str, IntegrationResponse] = {}
        self._lock = threading.RLock()

    def execute_action(self, request: IntegrationRequest) -> IntegrationResponse:
        """Execute an external action request through registered provider adapter."""
        # 1. Idempotency Check
        if request.idempotency_key:
            with self._lock:
                if request.idempotency_key in self._idempotency_cache:
                    cached = self._idempotency_cache[request.idempotency_key]
                    logger.info("Returned cached idempotent response for key '%s'", request.idempotency_key)
                    return cached.model_copy(deep=True)

        # 2. Get Connection & Integration Action
        conn = self._connection_service.get_connection(request.connection_id)
        if conn.status not in (ConnectionStatus.ACTIVE, ConnectionStatus.DEGRADED):
            raise ActionExecutionError(
                request.action_id,
                ErrorCode.AUTHORIZATION_ERROR.value,
                f"Connection '{conn.connection_id}' is in status '{conn.status.value}' and cannot execute actions.",
            )

        intg, action = self._registry.resolve_action(conn.integration_id, request.action_id)

        # 3. Rate Limit Check
        rate_key = f"conn:{conn.connection_id}"
        if not self._rate_limiter.check_and_record(rate_key):
            self._record_audit(request.owner_id, intg.integration_id, conn.connection_id, action.name, "RATE_LIMITED")
            raise RateLimitExceededError(conn.connection_id, retry_after_seconds=60.0)

        # 4. Module 15 Security Check (Authoritative!)
        is_allowed, dec_status, detail = self._security_adapter.check_permission(
            owner_id=request.owner_id,
            integration_id=intg.integration_id,
            action_id=action.name,
            risk_level=action.risk_level.value,
            arguments=request.arguments,
        )

        if dec_status == "REQUIRE_APPROVAL":
            self._notification_adapter.notify(
                owner_id=request.owner_id,
                title="Approval Required for Integration Action",
                body=f"Execution of '{action.name}' requires user approval (Request ID: {detail}).",
            )
            resp = IntegrationResponse(
                request_id=request.request_id,
                status="REQUIRES_APPROVAL",
                data={"approval_request_id": detail, "action_name": action.name},
                metadata={"message": "Action paused pending user approval."},
            )
            self._record_audit(request.owner_id, intg.integration_id, conn.connection_id, action.name, "REQUIRES_APPROVAL")
            return resp

        if not is_allowed:
            self._record_audit(request.owner_id, intg.integration_id, conn.connection_id, action.name, "DENIED")
            raise PermissionDeniedIntegrationError(action.name, detail or "Denied by security policy")

        # 5. Handle Dry Run
        if request.dry_run:
            plan = IntegrationResponse(
                request_id=request.request_id,
                status="DRY_RUN",
                data={
                    "plan": "Validated integration action dry run",
                    "integration_id": intg.integration_id,
                    "action_name": action.name,
                    "target_connection": conn.connection_id,
                    "arguments": request.arguments,
                    "risk_level": action.risk_level.value,
                },
            )
            self._record_audit(request.owner_id, intg.integration_id, conn.connection_id, action.name, "DRY_RUN")
            return plan

        # 6. Execute Provider Action
        provider = self._registry.get_provider(intg.integration_key)
        start_t = time.time()

        try:
            res = provider.execute_action(
                connection=conn,
                action_id=action.name,
                args=request.arguments,
                secret_store=self._secret_store,
                request_context=request.metadata,
            )
            elapsed_ms = (time.time() - start_t) * 1000.0
            res.latency_ms = round(elapsed_ms, 2)

            # Update connection last used time
            conn.last_used_at = datetime.now(UTC)
            self._connection_service._connection_repo.save(conn)

            # Store in idempotency cache if key present
            if request.idempotency_key:
                with self._lock:
                    self._idempotency_cache[request.idempotency_key] = res.model_copy(deep=True)

            self._record_audit(request.owner_id, intg.integration_id, conn.connection_id, action.name, "SUCCESS")
            return res

        except Exception as exc:
            elapsed_ms = (time.time() - start_t) * 1000.0
            logger.error("Error executing integration action '%s': %s", action.name, exc)
            self._record_audit(
                request.owner_id,
                intg.integration_id,
                conn.connection_id,
                action.name,
                f"FAILED: {str(exc)}",
            )
            raise
        return res

    def _record_audit(
        self, owner_id: str, integration_id: str, connection_id: str, action: str, result: str
    ) -> None:
        evt = IntegrationAuditEvent(
            owner_id=owner_id,
            integration_id=integration_id,
            connection_id=connection_id,
            action=action,
            result=result,
        )
        self._audit_repo.save(evt)
