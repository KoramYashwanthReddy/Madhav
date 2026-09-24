"""Browser Policy & Security Enforcement Service for Module 20.

Evaluates URL schemes, domain allowlists/blocklists, redirect security,
sensitive field masking, Prompt Injection Defense, Module 17 filesystem sandbox checks,
and Module 15 PermissionGate integration.
"""

import re
import uuid
from typing import Any
from urllib.parse import urlparse

from max.browser.domain.enums import (
    BrowserActionType,
)
from max.browser.domain.exceptions import (
    BrowserApprovalRequiredError,
    BrowserDomainBlockedError,
    BrowserNavigationBlockedError,
    BrowserPermissionDeniedError,
    BrowserSubsystemDisabledError,
)
from max.browser.domain.models import (
    BrowserObservation,
)
from max.config.sections import BrowserSettings
from max.security.domain.decision import PermissionRequest
from max.security.domain.enums import (
    PermissionAction,
    PermissionSubjectType,
    ResourceSensitivity,
    RiskLevel,
)
from max.security.domain.resource import PermissionResource
from max.security.domain.subject import PermissionSubject
from max.security.services.gate import PermissionGate

SENSITIVE_FIELD_PATTERNS = re.compile(
    r"(password|passwd|secret|api_?key|token|auth|credit_?card|cc_|card_number|cvv|ssn|social_?security|otp)",
    re.IGNORECASE,
)

PROMPT_INJECTION_PATTERNS = re.compile(
    r"(ignore\s+(previous|all)\s+instructions|reveal\s+(your\s+)?(system\s+prompt|credentials|secrets)|"
    r"disable\s+security|grant\s+access|upload\s+all\s+files|change\s+permissions)",
    re.IGNORECASE,
)

# Dangerous URL schemes that must always be blocked
_BLOCKED_SCHEMES = frozenset(["javascript", "data", "file", "about", "chrome", "edge", "devtools", "vbscript"])


class BrowserPolicyService:
    """Evaluates safety policies, URL security, Prompt Injection Defense, and permissions."""

    def __init__(
        self,
        settings: BrowserSettings | None = None,
        permission_gate: PermissionGate | None = None,
    ) -> None:
        self.settings = settings or BrowserSettings()
        self.permission_gate = permission_gate

    # ------------------------------------------------------------------
    # URL validation helpers (called by tests & service)
    # ------------------------------------------------------------------

    def validate_url_scheme(self, url: str) -> bool:
        """Validate URL scheme — returns True if safe, raises BrowserNavigationBlockedError if blocked."""
        parsed = urlparse(url)
        scheme = (parsed.scheme or "http").lower()

        if scheme in _BLOCKED_SCHEMES:
            raise BrowserNavigationBlockedError(
                f"Unsafe or blocked URL scheme '{scheme}:' detected. Navigation is not permitted."
            )
        if scheme not in self.settings.allowed_schemes:
            raise BrowserNavigationBlockedError(
                f"URL scheme '{scheme}:' is not in the allowed schemes list."
            )
        return True

    def validate_domain(self, url: str) -> None:
        """Validate domain against allow/blocklists. Raises BrowserDomainBlockedError if blocked."""
        parsed = urlparse(url)
        domain = (parsed.netloc or "").split(":")[0].lower()

        if not domain:
            return

        for blocked in self.settings.blocked_domains:
            blocked_lower = blocked.lower()
            if domain == blocked_lower or domain.endswith("." + blocked_lower):
                raise BrowserDomainBlockedError(
                    f"Domain {blocked_lower} is blocked by security policy."
                )

        if self.settings.allowed_domains and "*" not in self.settings.allowed_domains:
            allowed = any(
                domain == ok.lower() or domain.endswith("." + ok.lower())
                for ok in self.settings.allowed_domains
            )
            if not allowed:
                raise BrowserDomainBlockedError(
                    f"Domain '{domain}' is not in the allowed domains list."
                )

    def validate_url(self, url: str) -> None:
        """Full URL security validation: scheme + domain check."""
        if not self.settings.enabled:
            raise BrowserSubsystemDisabledError("Browser Agent subsystem is disabled.")
        self.validate_url_scheme(url)
        self.validate_domain(url)

    # ------------------------------------------------------------------
    # Sensitive field classification & masking
    # ------------------------------------------------------------------

    def is_sensitive_field(self, field_name: str, input_type: str = "") -> bool:
        """Return True if the field represents a sensitive input (password, token, etc.)."""
        if input_type.lower() in ("password", "secret"):
            return True
        return bool(SENSITIVE_FIELD_PATTERNS.search(field_name or ""))

    def mask_sensitive_value(self, value: str) -> str:
        """Return redaction sentinel if sensitive input masking is enabled."""
        if self.settings.redact_sensitive_inputs:
            return "[REDACTED_SENSITIVE_INPUT]"
        return value

    # ------------------------------------------------------------------
    # Prompt Injection Defense
    # ------------------------------------------------------------------

    def evaluate_web_content(self, text: str) -> dict[str, Any]:
        """Scan extracted web content for prompt injection patterns.

        Returns:
            dict with keys:
                - is_untrusted: always True for web content
                - has_injection: True if injection detected
                - sanitized_text: text with injection payloads replaced
        """
        has_injection = bool(PROMPT_INJECTION_PATTERNS.search(text))
        sanitized = text
        if has_injection:
            sanitized = PROMPT_INJECTION_PATTERNS.sub("[PROMPT_INJECTION_DEFENSE_TRIGGERED]", text)
        return {
            "is_untrusted": True,
            "has_injection": has_injection,
            "sanitized_text": sanitized,
        }

    def sanitize_observation(self, observation: BrowserObservation) -> BrowserObservation:
        """Inspect page observation for Prompt Injection attempts and sanitize content."""
        content = observation.text_content or ""
        match = PROMPT_INJECTION_PATTERNS.search(content)

        warning = None
        if match:
            warning = (
                f"PROMPT INJECTION WARNING: Untrusted page content contains suspicious text: "
                f"'{match.group(0)}'"
            )
            content = PROMPT_INJECTION_PATTERNS.sub("[PROMPT_INJECTION_DEFENSE_TRIGGERED]", content)

        return observation.model_copy(
            update={
                "text_content": content,
                "prompt_injection_warning": warning,
                "is_untrusted_web_content": True,
            }
        )

    # ------------------------------------------------------------------
    # Action permission validation
    # ------------------------------------------------------------------

    def validate_action(
        self,
        action_type: BrowserActionType,
        target_url: str | None = None,
        context: dict[str, Any] | None = None,
        owner_id: str = "system",
        agent_id: str | None = None,
    ) -> None:
        """Validate permission and policy before executing a browser action."""
        if not self.settings.enabled:
            raise BrowserSubsystemDisabledError("Browser Agent subsystem is disabled.")

        if target_url:
            self.validate_url(target_url)

        # Module 15 Permission Gate check
        if self.permission_gate is not None:
            risk = self._classify_risk(action_type, context)
            perm_req = PermissionRequest(
                request_id=f"bperm_{uuid.uuid4().hex[:12]}",
                owner_id=owner_id,
                subject=PermissionSubject(
                    subject_id=agent_id or "agent_browser",
                    subject_type=PermissionSubjectType.AGENT,
                ),
                resource=PermissionResource(
                    resource_type="BROWSER",
                    resource_id=f"browser.{action_type.value.lower()}",
                    owner_id=owner_id,
                    sensitivity=(
                        ResourceSensitivity.HIGHLY_SENSITIVE
                        if risk == RiskLevel.CRITICAL
                        else ResourceSensitivity.NORMAL
                    ),
                    attributes={"action_type": action_type.value, "url": target_url},
                ),
                action=PermissionAction.EXECUTE,
                risk_level=risk,
                tool_reference=f"browser.{action_type.value.lower()}",
            )
            decision = self.permission_gate.check(perm_req)
            if not decision.is_allowed:
                if getattr(decision, "requires_approval", False):
                    raise BrowserApprovalRequiredError(
                        f"Action '{action_type.value}' requires explicit human approval via Module 15."
                    )
                raise BrowserPermissionDeniedError(
                    f"Permission denied for browser action '{action_type.value}': {decision.reason}"
                )

    def _classify_risk(
        self, action_type: BrowserActionType, context: dict[str, Any] | None = None
    ) -> RiskLevel:
        """Classify operational risk level for Module 15 evaluation."""
        if action_type in (
            BrowserActionType.OBSERVE,
            BrowserActionType.EXTRACT_TEXT,
            BrowserActionType.EXTRACT_LINKS,
            BrowserActionType.EXTRACT_FORMS,
            BrowserActionType.SCREENSHOT,
            BrowserActionType.SWITCH_TAB,
        ):
            return RiskLevel.LOW

        if action_type in (
            BrowserActionType.NAVIGATE,
            BrowserActionType.BACK,
            BrowserActionType.FORWARD,
            BrowserActionType.RELOAD,
            BrowserActionType.SCROLL,
            BrowserActionType.WAIT,
            BrowserActionType.CLICK,
            BrowserActionType.TYPE,
            BrowserActionType.SELECT,
        ):
            return RiskLevel.MEDIUM

        return RiskLevel.HIGH
