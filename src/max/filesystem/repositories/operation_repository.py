"""Repository for tracking filesystem operations and their lifecycles."""

import threading

from max.filesystem.domain.action import FileOperation
from max.filesystem.domain.enums import FileOperationStatus


class FileOperationRepository:
    """Thread-safe in-memory repository for file operation records."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._operations: dict[str, FileOperation] = {}

    def save(self, operation: FileOperation) -> FileOperation:
        """Save or update a file operation."""
        with self._lock:
            self._operations[operation.request.operation_id] = operation
            return operation

    def get(self, operation_id: str) -> FileOperation | None:
        """Retrieve a file operation by ID."""
        with self._lock:
            return self._operations.get(operation_id)

    def list_all(
        self,
        status: FileOperationStatus | None = None,
        limit: int = 100,
    ) -> list[FileOperation]:
        """List operations with optional status filter and limit."""
        with self._lock:
            results = list(self._operations.values())
            if status is not None:
                results = [op for op in results if op.status == status]
            results.sort(key=lambda op: op.request.timestamp, reverse=True)
            return results[:limit]

    def clear(self) -> None:
        """Clear all stored operations (useful for testing)."""
        with self._lock:
            self._operations.clear()
