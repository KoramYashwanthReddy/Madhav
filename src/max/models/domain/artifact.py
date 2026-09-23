"""Model artifact metadata and safe path resolution entity."""

import hashlib
import uuid
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from max.models.domain.enums import ModelFormat


class ModelArtifact(BaseModel):
    """Model storage artifact descriptor."""

    artifact_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique artifact identifier",
    )
    model_id: str = Field(description="Associated model identifier")
    format: ModelFormat = Field(default=ModelFormat.UNKNOWN, description="Storage format")
    path: str | None = Field(
        default=None, description="Filesystem path string relative or absolute"
    )
    size_bytes: int | None = Field(default=None, description="File size in bytes", ge=0)
    checksum: str | None = Field(default=None, description="File checksum hash string")
    checksum_algorithm: str = Field(default="sha256", description="Checksum algorithm identifier")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Artifact registration timestamp",
    )
    status: str = Field(default="available", description="Artifact status indicator")


class ModelLocation:
    """Safe path resolution helper enforcing model root boundaries."""

    def __init__(self, root_directory: Path | str) -> None:
        self._root_directory: Path = Path(root_directory).resolve()

    @property
    def root_directory(self) -> Path:
        """Return canonical model root directory."""
        return self._root_directory

    def resolve_safe_path(self, target_path: Path | str) -> Path:
        """Resolve and validate that target path remains inside root directory boundary."""
        raw_path = Path(target_path)
        if raw_path.is_absolute():
            resolved = raw_path.resolve()
        else:
            resolved = (self._root_directory / raw_path).resolve()

        # Prevent path traversal outside model root directory
        try:
            resolved.relative_to(self._root_directory)
        except ValueError as exc:
            raise ValueError(
                f"Path traversal detected: Target path '{target_path}' "
                f"resolves outside root '{self._root_directory}'."
            ) from exc

        return resolved

    def verify_checksum(
        self, file_path: Path | str, expected_checksum: str, algorithm: str = "sha256"
    ) -> bool:
        """Verify SHA-256 checksum of local file."""
        resolved = self.resolve_safe_path(file_path)
        if not resolved.exists() or not resolved.is_file():
            return False

        hasher = hashlib.new(algorithm)
        with open(resolved, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)

        calculated = hasher.hexdigest().lower()
        return calculated == expected_checksum.lower()
