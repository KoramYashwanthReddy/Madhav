"""Policy Validator enforcing safety and permission boundaries for Module 31."""

import logging
from typing import Any

from max.personalization.domain.exceptions import (
    PermissionEscalationViolationError,
    SensitiveInferenceViolationError,
)

logger = logging.getLogger(__name__)

# Topics and keywords forbidden from automated behavioral inference
SENSITIVE_KEYWORDS = {
    # Medical & Health
    "medical", "health", "disease", "illness", "diagnosis", "medication", "doctor",
    "hospital", "treatment", "symptom", "cancer", "diabetes", "depressed", "depression",
    "anxiety", "bipolar", "mental_health", "psychiatric", "patient", "disability",
    # Political
    "political", "politics", "conservative", "liberal", "democrat", "republican",
    "communist", "socialist", "left-wing", "right-wing", "voting", "election", "party",
    # Religious
    "religion", "religious", "christian", "muslim", "jewish", "hindu", "buddhist",
    "atheist", "agnostic", "faith", "church", "mosque", "synagogue", "temple", "prayer",
    # Sexual orientation & Identity
    "sexual_orientation", "sexuality", "gay", "lesbian", "bisexual", "transgender",
    "queer", "lgbt", "gender_identity",
    # Protected characteristics
    "ethnicity", "race", "racial", "caste", "national_origin", "skin_color",
}

# Key patterns associated with security authority that learning MUST NOT alter
SECURITY_ESCALATION_KEYWORDS = {
    "permission", "permissions", "allow", "grant", "bypass", "unrestricted",
    "root", "sudo", "admin", "shell_execution", "credential", "security_policy",
    "security_mode", "authorization", "privilege", "override_security",
}


class PolicyValidator:
    """Enforces strict safety boundaries on learning and personalization."""

    def __init__(self, allow_sensitive_inference: bool = False) -> None:
        self.allow_sensitive_inference = allow_sensitive_inference

    def validate_hypothesis(
        self,
        category: str,
        key: str,
        proposed_value: Any,
        observation: str = "",
        raise_on_violation: bool = True,
    ) -> bool:
        """Validate an inferred preference hypothesis against safety boundaries."""
        # 1. Check for security / permission escalation attempts
        if self._is_security_escalation(category, key, proposed_value, observation):
            logger.warning(
                "Policy violation: Preference hypothesis attempts to alter security authority! Key: %s", key
            )
            if raise_on_violation:
                raise PermissionEscalationViolationError(
                    f"Learning cannot modify security policy or grant permissions. Key: '{key}'",
                    details={"category": category, "key": key, "proposed_value": proposed_value},
                )
            return False

        # 2. Check for sensitive personal inference
        if not self.allow_sensitive_inference and self._is_sensitive_inference(
            category, key, proposed_value, observation
        ):
            logger.warning(
                "Policy violation: Preference hypothesis infers forbidden sensitive personal characteristic! Key: %s", key
            )
            if raise_on_violation:
                raise SensitiveInferenceViolationError(
                    f"Learning cannot infer or store sensitive personal traits. Key: '{key}'",
                    details={"category": category, "key": key, "proposed_value": proposed_value},
                )
            return False

        return True

    def validate_preference_creation(
        self, category: str, key: str, value: Any, source_is_explicit: bool = False
    ) -> bool:
        """Validate user or system preference creation."""
        # Security boundaries apply to ALL preferences (even explicit ones cannot override Module 15 authority)
        if self._is_security_escalation(category, key, value, ""):
            raise PermissionEscalationViolationError(
                f"Preference cannot alter security policy or grant security permissions. Key: '{key}'",
                details={"category": category, "key": key, "value": value},
            )

        if not source_is_explicit and self._is_sensitive_inference(category, key, value, ""):
            raise SensitiveInferenceViolationError(
                f"Inferred preference contains forbidden sensitive characteristics. Key: '{key}'",
                details={"category": category, "key": key, "value": value},
            )

        return True

    def _is_security_escalation(
        self, category: str, key: str, value: Any, observation: str
    ) -> bool:
        text_content = f"{category} {key} {str(value)} {observation}".lower()
        for kw in SECURITY_ESCALATION_KEYWORDS:
            if kw in text_content:
                # Check if it's attempting to GRANT or BYPASS security permissions
                if any(
                    grant_kw in text_content
                    for grant_kw in ["allow", "bypass", "unrestricted", "grant", "always_approve", "no_confirm"]
                ) or kw in ["shell_execution", "security_policy", "security_mode", "credential"]:
                    return True
        return False

    def _is_sensitive_inference(
        self, category: str, key: str, value: Any, observation: str
    ) -> bool:
        text_content = f"{category} {key} {str(value)} {observation}".lower()
        words = set(text_content.replace("_", " ").replace("-", " ").split())
        for kw in SENSITIVE_KEYWORDS:
            if kw in words or kw in text_content:
                return True
        return False
