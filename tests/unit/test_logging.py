"""Unit tests for structured logging and sensitive data masking."""

import json
import logging

from max.core.logging import JSONLogFormatter, mask_sensitive_data
from max.core.request_id import set_request_id


def test_mask_sensitive_data() -> None:
    """Test masking secrets and sensitive header values."""
    raw_token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    masked = mask_sensitive_data(raw_token)
    assert "eyJhbGci" not in masked
    assert "***MASKED***" in masked

    raw_password = "User logged in with password='SecretPassword123!'"
    masked_pw = mask_sensitive_data(raw_password)
    assert "SecretPassword123!" not in masked_pw
    assert "***MASKED***" in masked_pw


def test_json_log_formatter() -> None:
    """Test JSONLogFormatter produces valid JSON with required fields."""
    set_request_id("test-req-id-12345")
    formatter = JSONLogFormatter()
    record = logging.LogRecord(
        name="max.test",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test structured log output",
        args=(),
        exc_info=None,
    )

    formatted_output = formatter.format(record)
    log_json = json.loads(formatted_output)

    assert log_json["level"] == "INFO"
    assert log_json["logger"] == "max.test"
    assert log_json["message"] == "Test structured log output"
    assert log_json["service"] == "max"
    assert log_json["request_id"] == "test-req-id-12345"
    assert "timestamp" in log_json
