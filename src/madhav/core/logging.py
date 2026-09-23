"""Structured JSON logging foundation for MADHAV platform."""

import datetime
import json
import logging
import re
import sys
from typing import Any

from madhav.core.request_id import get_request_id
from madhav.version import SERVICE_NAME

# Regex patterns for masking sensitive information in log output
_SENSITIVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)(bearer\s+)[a-zA-Z0-9_\-\.=]+"),
    re.compile(
        r"(?i)(password|passwd|secret|api_key|apikey|token|authorization)\s*[:=]\s*['\"]?[^'\"\s,&]+['\"]?"
    ),
]


def mask_sensitive_data(text: str) -> str:
    """Sanitize log text to prevent leaking sensitive secrets or credentials."""
    sanitized = text
    for pattern in _SENSITIVE_PATTERNS:
        sanitized = pattern.sub(r"\1***MASKED***", sanitized)
    return sanitized


class JSONLogFormatter(logging.Formatter):
    """Custom JSON log formatter producing structured log entries."""

    def format(self, record: logging.LogRecord) -> str:
        log_message = record.getMessage()
        sanitized_message = mask_sensitive_data(log_message)

        log_data: dict[str, Any] = {
            "timestamp": datetime.datetime.fromtimestamp(
                record.created, tz=datetime.UTC
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": sanitized_message,
            "service": SERVICE_NAME,
            "request_id": get_request_id(),
        }

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            log_data["exception"] = mask_sensitive_data(record.exc_text)

        extra_dict = getattr(record, "extra", None)
        if isinstance(extra_dict, dict):
            for key, val in extra_dict.items():
                if key not in log_data:
                    log_data[key] = val

        return json.dumps(log_data)


def setup_logging(level: str | Any = "INFO", json_format: bool = True) -> logging.Logger:
    """Configure structured logging for MADHAV application."""
    level_str = str(level).upper() if level else "INFO"
    numeric_level = getattr(logging, level_str, logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove pre-existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    if json_format:
        console_handler.setFormatter(JSONLogFormatter())
    else:
        fmt = "%(asctime)s [%(levelname)s] %(name)s (request_id=%(request_id)s): %(message)s"
        console_handler.setFormatter(logging.Formatter(fmt))

    root_logger.addHandler(console_handler)
    return logging.getLogger(SERVICE_NAME)
