"""Centralized secret and sensitive data redaction service for Module 33 — Observability & Audit."""

import hashlib
import re
from typing import Any

SENSITIVE_KEY_PATTERNS = {
    "password",
    "pass",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "jwt",
    "cookie",
    "authorization",
    "auth",
    "private_key",
    "privatekey",
    "client_secret",
    "db_password",
    "smtp_password",
    "credential",
    "credentials",
    "webhook_secret",
    "payment_credential",
}

DEFAULT_REDACTED_PLACEHOLDER = "[REDACTED]"


class RedactionService:
    """Centralized redaction layer for protecting credentials, secrets, and private data."""

    def __init__(
        self,
        custom_sensitive_keys: set[str] | None = None,
        redaction_placeholder: str = DEFAULT_REDACTED_PLACEHOLDER,
        enabled: bool = True,
    ) -> None:
        self.sensitive_keys = set(SENSITIVE_KEY_PATTERNS)
        if custom_sensitive_keys:
            self.sensitive_keys.update(k.lower() for k in custom_sensitive_keys)
        self.redaction_placeholder = redaction_placeholder
        self.enabled = enabled

    def is_sensitive_key(self, key_name: str) -> bool:
        """Check if a dictionary key name matches sensitive patterns."""
        normalized = key_name.lower().replace("-", "_")
        return any(pattern in normalized for pattern in self.sensitive_keys)

    def redact_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively redact sensitive key-value pairs in a dictionary."""
        if not self.enabled or not isinstance(data, dict):
            return data

        redacted: dict[str, Any] = {}
        for key, value in data.items():
            if self.is_sensitive_key(str(key)):
                redacted[key] = self.redaction_placeholder
            elif isinstance(value, dict):
                redacted[key] = self.redact_dict(value)
            elif isinstance(value, list):
                redacted[key] = [
                    self.redact_dict(v) if isinstance(v, dict) else self._redact_scalar_if_needed(v)
                    for v in value
                ]
            else:
                redacted[key] = self._redact_scalar_if_needed(value)
        return redacted

    def _redact_scalar_if_needed(self, val: Any) -> Any:
        """Check text scalars for obvious secret patterns like Bearer tokens or private keys."""
        if isinstance(val, str):
            if val.startswith("Bearer ") or val.startswith("bearer "):
                return f"Bearer {self.redaction_placeholder}"
            if "-----BEGIN PRIVATE KEY-----" in val or "-----BEGIN RSA PRIVATE KEY-----" in val:
                return self.redaction_placeholder
        return val

    def redact_text(self, text: str) -> str:
        """Redact known secret patterns inside raw text blocks."""
        if not self.enabled or not text:
            return text

        # Redact Authorization header values
        text = re.sub(r"(Authorization:\s*Bearer\s+)[^\s]+", r"\1" + self.redaction_placeholder, text, flags=re.IGNORECASE)
        # Redact API keys or passwords in key=val, key: val, or key is val patterns
        for key in self.sensitive_keys:
            text = re.sub(
                rf"({key}[\"']?\s*(?:[:=]|\bis\b)\s*[\"']?)[^\"'\s,\.]+",
                rf"\1{self.redaction_placeholder}",
                text,
                flags=re.IGNORECASE,
            )
        return text

    def sanitize_log_message(self, message: str) -> str:
        """Prevent log injection by escaping newlines and control characters, and redacting secrets."""
        if not message:
            return ""

        # Normalize/escape control chars and newlines to prevent log injection
        cleaned = message.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
        cleaned = "".join(ch if ord(ch) >= 32 or ch == "\t" else f"\\x{ord(ch):02x}" for ch in cleaned)

        return self.redact_text(cleaned)

    def redact_ai_content(
        self, content: str, capture_enabled: bool = False, max_preview_len: int = 100
    ) -> dict[str, Any]:
        """Privacy handler for AI prompts and responses."""
        if not content:
            return {"content_hash": "", "preview": ""}

        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        if capture_enabled:
            return {
                "content_hash": content_hash,
                "full_content": self.redact_text(content),
                "opt_in_captured": True,
            }

        # Production privacy default: store content hash and truncated preview only
        redacted_content = self.redact_text(content)
        preview = (
            redacted_content[:max_preview_len] + "..."
            if len(redacted_content) > max_preview_len
            else redacted_content
        )
        return {
            "content_hash": content_hash,
            "preview": preview,
            "content_length": len(content),
            "opt_in_captured": False,
        }
