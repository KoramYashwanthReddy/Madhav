"""Memory content domain model."""

import hashlib
import json
from typing import Any

from pydantic import BaseModel, Field, field_validator


class MemoryContent(BaseModel):
    """Structured memory content representation."""

    text: str = Field(description="Primary text payload of memory")
    structured_data: dict[str, Any] = Field(
        default_factory=dict, description="Optional key-value structured data"
    )
    content_type: str = Field(default="text/plain", description="MIME content-type indicator")

    @field_validator("text")
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        """Ensure memory text is non-empty and stripped of outer whitespace."""
        if not v or not v.strip():
            raise ValueError("Memory content text cannot be empty or whitespace-only.")
        return v.strip()

    @property
    def content_hash(self) -> str:
        """Compute SHA-256 digest of normalized text and sorted structured data."""
        normalized_text = " ".join(self.text.split()).lower()
        struct_json = (
            json.dumps(self.structured_data, sort_keys=True) if self.structured_data else ""
        )
        raw = f"{normalized_text}|{struct_json}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
