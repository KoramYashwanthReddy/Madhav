"""Task dependency domain model."""

from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from max.tasks.domain.enums import DependencyType


class TaskDependency(BaseModel):
    """Directed dependency relationship edge between two tasks."""

    model_config = ConfigDict(frozen=True)

    dependency_id: str = Field(default_factory=lambda: f"dep_{uuid4().hex[:12]}", description="Unique dependency ID")
    source_task_id: str = Field(description="Task ID that is dependent or source of relationship")
    target_task_id: str = Field(description="Task ID that must be completed or target of relationship")
    dependency_type: DependencyType = Field(
        default=DependencyType.DEPENDS_ON, description="Dependency relationship type"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
