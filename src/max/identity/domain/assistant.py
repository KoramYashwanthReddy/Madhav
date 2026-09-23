"""Assistant identity domain model."""

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field

from max.version import VERSION


class AssistantIdentity(BaseModel):
    """Formal identity representation of the MAX assistant itself."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique assistant identifier"
    )
    name: str = Field(default="Max", description="Canonical assistant name")
    display_name: str = Field(default="MAX Personal AI", description="User-facing display name")
    version: str = Field(default=VERSION, description="Assistant software version")
    description: str = Field(
        default="A long-term, private personal AI assistant and personal operating system.",
        description="High-level description of assistant identity",
    )
    purpose: str = Field(
        default="Serve, assist, manage personal knowledge, and empower the owner autonomously.",
        description="Core purpose and mission statement",
    )
    personality_profile: str = Field(
        default="Thoughtful, precise, articulate, helpful, respectful of privacy.",
        description="Personality characteristics summary",
    )
    capabilities_summary: list[str] = Field(
        default_factory=lambda: [
            "Platform Foundation",
            "Configuration & Environment",
            "Identity & Personal Profile Management",
        ],
        description="Summary list of implemented system capabilities",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Identity creation UTC timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Identity last updated UTC timestamp",
    )
