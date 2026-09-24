"""Data Classification Engine and Sensitivity Taxonomy."""

import enum
from typing import Any
from pydantic import BaseModel, Field


class ClassificationLevel(str, enum.Enum):
    """Sensitivity taxonomy classification levels for MAX platform data."""

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    SENSITIVE = "SENSITIVE"
    CONFIDENTIAL = "CONFIDENTIAL"
    CRITICAL = "CRITICAL"


class DataClassificationTag(BaseModel):
    """Classification tag associated with stored data payloads or database entities."""

    level: ClassificationLevel = Field(default=ClassificationLevel.INTERNAL, description="Sensitivity level classification")
    retention_days: int = Field(default=90, description="Recommended retention window in days")
    encrypted_at_rest: bool = Field(default=False, description="Whether data payload requires field/storage encryption")
    contains_pii: bool = Field(default=False, description="Whether payload contains personally identifiable information")
    policy_notes: str | None = Field(default=None, description="Additional compliance or retention notes")


class DataClassifier:
    """Engine for classifying data payloads according to privacy, sensitivity, and retention rules."""

    SENSITIVE_KEY_NAMES = {
        "password",
        "secret",
        "api_key",
        "private_key",
        "token",
        "ssn",
        "credit_card",
        "auth_token",
        "credentials",
    }

    CONFIDENTIAL_DOMAINS = {
        "memory",
        "credentials",
        "identity",
        "audit_logs",
    }

    @classmethod
    def classify_domain(cls, domain_name: str) -> DataClassificationTag:
        """Classify data entity by subsystem domain name."""
        domain_lower = domain_name.lower()

        if domain_lower in ("identity", "security", "credentials"):
            return DataClassificationTag(
                level=ClassificationLevel.CRITICAL,
                retention_days=365,
                encrypted_at_rest=True,
                contains_pii=True,
                policy_notes="Critical platform security boundary; mandatory AES-256 encryption.",
            )
        elif domain_lower in ("memory", "conversation", "personalization"):
            return DataClassificationTag(
                level=ClassificationLevel.CONFIDENTIAL,
                retention_days=180,
                encrypted_at_rest=True,
                contains_pii=True,
                policy_notes="Personal user memory and conversation history; strict confidentiality.",
            )
        elif domain_lower in ("knowledge", "document", "rag"):
            return DataClassificationTag(
                level=ClassificationLevel.SENSITIVE,
                retention_days=365,
                encrypted_at_rest=False,
                contains_pii=False,
                policy_notes="User personal knowledge documents and embeddings.",
            )
        elif domain_lower in ("observability", "metrics", "logs"):
            return DataClassificationTag(
                level=ClassificationLevel.INTERNAL,
                retention_days=90,
                encrypted_at_rest=False,
                contains_pii=False,
                policy_notes="Operational metrics and telemetry data.",
            )
        else:
            return DataClassificationTag(
                level=ClassificationLevel.INTERNAL,
                retention_days=90,
                encrypted_at_rest=False,
                contains_pii=False,
            )

    @classmethod
    def classify_payload(cls, data: dict[str, Any]) -> DataClassificationTag:
        """Inspect dictionary payload fields for sensitive tokens or PII indicators."""
        keys = set(str(k).lower() for k in data.keys())

        if keys.intersection(cls.SENSITIVE_KEY_NAMES):
            return DataClassificationTag(
                level=ClassificationLevel.CRITICAL,
                retention_days=365,
                encrypted_at_rest=True,
                contains_pii=True,
                policy_notes="Payload contains high-risk authentication tokens or credentials.",
            )

        return DataClassificationTag(
            level=ClassificationLevel.INTERNAL,
            retention_days=90,
            encrypted_at_rest=False,
            contains_pii=False,
        )
