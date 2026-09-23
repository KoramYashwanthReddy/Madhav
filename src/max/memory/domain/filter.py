"""Memory search query filter specification model."""

from datetime import datetime

from pydantic import BaseModel, Field

from max.memory.domain.enums import (
    MemoryImportance,
    MemorySource,
    MemoryStatus,
    MemoryType,
)


class MemorySearchFilter(BaseModel):
    """Query specification parameters for searching and filtering memory records."""

    query: str | None = Field(default=None, description="Case-insensitive text substring match")
    types: list[MemoryType] | None = Field(
        default=None, description="Filter by one or more memory types"
    )
    statuses: list[MemoryStatus] | None = Field(
        default=None, description="Filter by explicit memory statuses"
    )
    importances: list[MemoryImportance] | None = Field(
        default=None, description="Filter by importance levels"
    )
    sources: list[MemorySource] | None = Field(
        default=None, description="Filter by memory source origins"
    )
    tags: list[str] | None = Field(default=None, description="Filter by indexing tags")
    owner_id: str = Field(default="default_owner", description="Owner identity scoping filter")
    created_after: datetime | None = Field(
        default=None, description="Filter memories created at or after this UTC timestamp"
    )
    created_before: datetime | None = Field(
        default=None, description="Filter memories created at or before this UTC timestamp"
    )
    include_expired: bool = Field(
        default=False, description="Flag indicating whether to include EXPIRED records"
    )
    include_archived: bool = Field(
        default=False, description="Flag indicating whether to include ARCHIVED records"
    )
    include_deleted: bool = Field(
        default=False, description="Flag indicating whether to include soft DELETED records"
    )
    limit: int = Field(default=50, description="Pagination page limit")
    offset: int = Field(default=0, description="Pagination page offset")
