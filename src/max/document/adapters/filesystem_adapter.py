"""Filesystem adapter for Module 24 — Document Intelligence."""

import logging
import os
from typing import Any

from max.document.domain.exceptions import DocumentSecurityError
from max.filesystem.domain.action import FileOperationRequest
from max.filesystem.domain.enums import FileOperationType

logger = logging.getLogger(__name__)


class DocumentFilesystemAdapter:
    """Routes filesystem access through Module 17 FilesystemService."""

    def __init__(self, filesystem_service: Any | None = None) -> None:
        self._fs = filesystem_service

    async def read_bytes(self, file_path: str, owner_id: str = "user_default") -> bytes:
        """Read raw bytes from specified path, routing through Module 17 if available."""
        abs_path = os.path.abspath(file_path)

        if self._fs is not None:
            req = FileOperationRequest(
                operation_type=FileOperationType.READ_FILE,
                target_path=abs_path,
                owner_id=owner_id,
            )
            result = await self._fs.execute_operation(req)
            if not result.success or result.content is None:
                raise DocumentSecurityError(
                    f"Filesystem agent denied read access to '{file_path}': {result.error_message}",
                    details={"path": file_path},
                )
            if isinstance(result.content, bytes):
                return result.content
            return str(result.content).encode("utf-8")

        # Direct read fallback if FilesystemService is omitted
        if not os.path.isfile(abs_path):
            raise DocumentSecurityError(
                f"File not found or unreadable: '{file_path}'",
                details={"path": file_path},
            )
        with open(abs_path, "rb") as f:
            return f.read()

    async def write_bytes(self, file_path: str, content: bytes, owner_id: str = "user_default") -> None:
        """Write raw bytes to specified path, routing through Module 17 if available."""
        abs_path = os.path.abspath(file_path)

        if self._fs is not None:
            req = FileOperationRequest(
                operation_type=FileOperationType.WRITE_FILE,
                target_path=abs_path,
                content=content.decode("utf-8", errors="replace"),
                owner_id=owner_id,
            )
            result = await self._fs.execute_operation(req)
            if not result.success:
                raise DocumentSecurityError(
                    f"Filesystem agent denied write access to '{file_path}': {result.error_message}",
                    details={"path": file_path},
                )
            return

        # Direct write fallback
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "wb") as f:
            f.write(content)
