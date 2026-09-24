"""PatchService for diff preview, patch application, stale-patch detection, and rollback."""

import difflib
import hashlib
import os
from datetime import UTC

from max.coding.domain.enums import ChangeType
from max.coding.domain.exceptions import RollbackFailedError, StalePatchError
from max.coding.domain.models import ChangeSet, Patch, PatchHunk
from max.coding.security.prompt_injection import CodeSecurityEnforcer
from max.filesystem.container import get_filesystem_container
from max.filesystem.domain.action import FileOperationRequest
from max.filesystem.domain.enums import FileOperationStatus, FileOperationType
from max.filesystem.services.filesystem_service import FilesystemService


def _hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


class PatchService:
    """Manages diff generation, patch application via FilesystemService, stale patch detection, and rollback."""

    def __init__(self, filesystem_service: FilesystemService | None = None) -> None:
        if filesystem_service is not None:
            self.fs_service = filesystem_service
        else:
            self.fs_service = get_filesystem_container().filesystem_service

    def generate_diff_preview(self, original_text: str, new_text: str, file_path: str) -> str:
        """Generate unified diff text representation for patch preview."""
        orig_lines = original_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        diff = difflib.unified_diff(
            orig_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
        )
        return "".join(diff)

    def create_patch(
        self,
        file_path: str,
        original_text: str,
        new_text: str,
        change_type: ChangeType = ChangeType.MODIFY_FILE,
        reason: str = "Code modification",
    ) -> Patch:
        """Construct a Patch object from original and modified content."""
        CodeSecurityEnforcer.validate_file_path(file_path)

        orig_hash = _hash_content(original_text) if original_text else ""
        hunk = PatchHunk(
            start_line=1,
            end_line=len(original_text.splitlines()) if original_text else 1,
            old_content=original_text,
            new_content=new_text,
        )

        return Patch(
            change_type=change_type,
            file_path=file_path,
            hunks=[hunk],
            original_content_hash=orig_hash,
            new_content=new_text if change_type == ChangeType.CREATE_FILE else None,
            reason=reason,
        )

    async def apply_changeset(self, repo_root: str, changeset: ChangeSet) -> None:
        """Apply a ChangeSet to the repository with stale patch verification and rollback backup."""
        if changeset.is_applied:
            return

        # Phase 1: Validate all target files and check for stale content
        for patch in changeset.patches:
            full_path = os.path.join(repo_root, patch.file_path)
            CodeSecurityEnforcer.validate_file_path(full_path)

            if patch.change_type in (ChangeType.MODIFY_FILE, ChangeType.DELETE_FILE):
                if os.path.exists(full_path):
                    current_text = ""
                    try:
                        read_req = FileOperationRequest(
                            operation_type=FileOperationType.READ_FILE,
                            source=full_path,
                            owner_id="system",
                        )
                        res = self.fs_service.execute_operation(read_req)
                        if res.status != FileOperationStatus.FAILED:
                            current_text = res.observed_state.get("content", "")
                            if isinstance(current_text, bytes):
                                current_text = current_text.decode("utf-8", errors="replace")
                    except Exception:
                        pass

                    if not current_text and os.path.exists(full_path):
                        with open(full_path, encoding="utf-8", errors="replace") as f:
                            current_text = f.read()

                    # Stale patch detection check
                    if patch.original_content_hash and _hash_content(current_text) != patch.original_content_hash:
                        raise StalePatchError(patch.file_path)

                    # Save pre-patch original content into backup_data for rollback
                    changeset.backup_data[patch.file_path] = current_text
                else:
                    raise StalePatchError(f"{patch.file_path} (file missing)")

        # Phase 2: Execute file writes / creations via FilesystemService
        for patch in changeset.patches:
            full_path = os.path.join(repo_root, patch.file_path)

            if patch.change_type in (ChangeType.CREATE_FILE, ChangeType.MODIFY_FILE):
                content_to_write = patch.new_content or (patch.hunks[0].new_content if patch.hunks else "")
                op_type = (
                    FileOperationType.CREATE_FILE
                    if patch.change_type == ChangeType.CREATE_FILE
                    else FileOperationType.WRITE_FILE
                )
                try:
                    write_req = FileOperationRequest(
                        operation_type=op_type,
                        source=full_path,
                        owner_id="system",
                        parameters={"content": content_to_write},
                    )
                    self.fs_service.execute_operation(write_req)
                except Exception:
                    pass

                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content_to_write)
            elif patch.change_type == ChangeType.DELETE_FILE:
                if os.path.exists(full_path):
                    try:
                        del_req = FileOperationRequest(
                            operation_type=FileOperationType.DELETE_FILE,
                            source=full_path,
                            owner_id="system",
                        )
                        self.fs_service.execute_operation(del_req)
                    except Exception:
                        pass
                    if os.path.exists(full_path):
                        os.remove(full_path)

        changeset.is_applied = True
        from datetime import datetime

        changeset.applied_at = datetime.now(UTC)

    async def rollback_changeset(self, repo_root: str, changeset: ChangeSet) -> None:
        """Rollback an applied ChangeSet by restoring original file content from backup_data."""
        if not changeset.is_applied:
            return

        try:
            for patch in changeset.patches:
                full_path = os.path.join(repo_root, patch.file_path)
                CodeSecurityEnforcer.validate_file_path(full_path)

                if patch.change_type == ChangeType.CREATE_FILE:
                    if os.path.exists(full_path):
                        try:
                            del_req = FileOperationRequest(
                                operation_type=FileOperationType.DELETE_FILE,
                                source=full_path,
                                owner_id="system",
                            )
                            self.fs_service.execute_operation(del_req)
                        except Exception:
                            pass
                        if os.path.exists(full_path):
                            os.remove(full_path)
                elif patch.change_type in (ChangeType.MODIFY_FILE, ChangeType.DELETE_FILE):
                    if patch.file_path in changeset.backup_data:
                        orig_text = changeset.backup_data[patch.file_path]
                        try:
                            write_req = FileOperationRequest(
                                operation_type=FileOperationType.WRITE_FILE,
                                source=full_path,
                                owner_id="system",
                                parameters={"content": orig_text},
                            )
                            self.fs_service.execute_operation(write_req)
                        except Exception:
                            pass
                        with open(full_path, "w", encoding="utf-8") as f:
                            f.write(orig_text)

            changeset.is_applied = False

        except Exception as e:
            raise RollbackFailedError(changeset.id, str(e))
