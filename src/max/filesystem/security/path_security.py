"""PathSecurityService for enforcing filesystem path normalization, sandbox boundaries, protected paths, and symlink security."""

from pathlib import Path

from max.config.sections import FilesystemSettings
from max.filesystem.domain.enums import FileType
from max.filesystem.domain.exceptions import (
    PathTraversalError,
    PathValidationError,
    ProtectedPathError,
    SandboxViolationError,
    SymlinkEscapeError,
)
from max.filesystem.domain.models import PathReference


class PathSecurityService:
    """Security service validating filesystem paths against sandbox boundaries and protected paths."""

    def __init__(self, settings: FilesystemSettings) -> None:
        self._settings = settings

    @property
    def allowed_roots(self) -> list[Path]:
        """Get allowed root paths."""
        return [Path(r).resolve() for r in self._settings.allowed_roots]

    @property
    def read_only_roots(self) -> list[Path]:
        """Get read-only root paths."""
        return [Path(r).resolve() for r in self._settings.read_only_roots]

    @property
    def blocked_roots(self) -> list[Path]:
        """Get blocked root paths."""
        return [Path(r).resolve() for r in self._settings.blocked_roots]

    def verify_path_access(
        self, raw_path: str, is_write: bool = False
    ) -> PathReference:
        """Normalize, resolve, and validate path against security boundaries."""
        if not raw_path or not raw_path.strip():
            raise PathValidationError("Path string cannot be empty.")

        path_str = raw_path.strip()

        # 1. Traversal check on raw path string
        if ".." in path_str.replace("\\", "/").split("/"):
            try:
                Path(path_str).resolve()
            except Exception as exc:
                raise PathTraversalError(f"Path resolution error for '{path_str}': {exc}") from exc

        try:
            path_obj = Path(path_str)
            norm_str = str(path_obj)
            resolved_obj = path_obj.resolve()
            resolved_str = str(resolved_obj)
        except Exception as exc:
            raise PathValidationError(f"Invalid path format '{path_str}': {exc}") from exc

        # 2. Check protected system paths
        self._check_protected_paths(resolved_obj)

        # 3. Check blocked roots
        self._check_blocked_roots(resolved_obj)

        # 4. Check allowed sandbox roots (if allowed_roots configured)
        allowed_root = self._check_allowed_roots(resolved_obj)

        # 5. Check read-only roots for mutations
        if is_write:
            self._check_read_only_roots(resolved_obj)

        # 6. Check symlink escape
        is_symlink = False
        try:
            is_symlink = path_obj.is_symlink()
        except Exception:
            pass

        if is_symlink:
            try:
                target_obj = path_obj.resolve(strict=True)
                self._check_allowed_roots(target_obj)
            except SandboxViolationError as exc:
                raise SymlinkEscapeError(f"Symlink '{path_str}' target resolves outside allowed sandbox root.") from exc
            except Exception:
                pass  # Broken symlink handled gracefully by backend

        ftype = FileType.DIRECTORY if resolved_obj.is_dir() else FileType.REGULAR_FILE

        return PathReference(
            original_path=path_str,
            normalized_path=norm_str,
            resolved_path=resolved_str,
            is_absolute=path_obj.is_absolute(),
            file_type=ftype,
            is_symlink=is_symlink,
            symlink_target=str(path_obj.resolve()) if is_symlink else None,
            allowed_root=allowed_root,
        )

    def verify_dual_path_access(
        self, source_raw: str, dest_raw: str, is_move_or_rename: bool = False
    ) -> tuple[PathReference, PathReference]:
        """Validate both source and destination paths for COPY, MOVE, RENAME operations."""
        src_ref = self.verify_path_access(source_raw, is_write=is_move_or_rename)
        dest_ref = self.verify_path_access(dest_raw, is_write=True)
        return src_ref, dest_ref

    def is_sensitive_path(self, resolved_path: str) -> bool:
        """Check if path matches configured sensitive path patterns (e.g. .env, keys, credentials)."""
        lower_p = resolved_path.lower()
        patterns = [".env", ".pem", ".key", "credentials", "secrets", "tokens", "id_rsa"]
        return any(pat in lower_p for pat in patterns)

    def _check_protected_paths(self, resolved_path: Path) -> None:
        """Check if resolved path targets protected system directories."""
        if not self._settings.sensitive_path_protection:
            return

        res_str = str(resolved_path).lower().replace("\\", "/")
        no_drive_str = res_str[2:] if len(res_str) >= 2 and res_str[1] == ":" else res_str

        protected_patterns = [
            "c:/windows",
            "c:/program files",
            "c:/program files (x86)",
            "c:/programdata",
            "c:/boot",
            "/etc",
            "/usr",
            "/boot",
            "/sys",
            "/proc",
            "/var/log",
        ]

        for p_pat in protected_patterns:
            if (
                res_str == p_pat
                or res_str.startswith(p_pat + "/")
                or no_drive_str == p_pat
                or no_drive_str.startswith(p_pat + "/")
            ):
                raise ProtectedPathError(f"Access to protected system path '{resolved_path}' is denied.")

    def _check_blocked_roots(self, resolved_path: Path) -> None:
        """Check if path falls under an explicitly blocked root."""
        for b_obj in self.blocked_roots:
            if self._is_subpath(resolved_path, b_obj):
                raise SandboxViolationError(f"Path '{resolved_path}' is under blocked root '{b_obj}'.")

    def _check_allowed_roots(self, resolved_path: Path) -> str | None:
        """Verify path is under an allowed sandbox root if allowed_roots is defined."""
        allowed = self.allowed_roots
        if not allowed:
            return None

        for a_obj in allowed:
            if self._is_subpath(resolved_path, a_obj):
                return str(a_obj)

        raise SandboxViolationError(f"Path '{resolved_path}' is outside configured allowed sandbox roots.")

    def _check_read_only_roots(self, resolved_path: Path) -> None:
        """Check if mutation operation targets a read-only root."""
        for ro_obj in self.read_only_roots:
            if self._is_subpath(resolved_path, ro_obj):
                raise SandboxViolationError(
                    f"Mutation denied on path under read-only root '{ro_obj}'."
                )

    def _is_subpath(self, target: Path, root: Path) -> bool:
        """Return True if target is equal to or subpath of root."""
        try:
            target.relative_to(root)
            return True
        except ValueError:
            target_str = str(target).lower().replace("\\", "/")
            root_str = str(root).lower().replace("\\", "/")
            return target_str == root_str or target_str.startswith(root_str.rstrip("/") + "/")
