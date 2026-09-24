# Module 17 — Filesystem Agent

## 1. Purpose
The Filesystem Agent gives Max controlled, permission-aware, auditable access to local filesystem resources. It enables safe execution of filesystem inspection, search, reading, writing, appending, copying, moving, renaming, comparison, and deletion within strict security boundaries.

## 2. Architecture
The Filesystem Agent strictly enforces that it is **not** the security authority. All operations pass through path normalization, sandbox root validation, symlink escape detection, and Module 15 authorization before reaching OS-level filesystem backends.

```
Agent Engine (Module 13)
        ↓
Tool Registry (Module 14)
        ↓
Permission & Security Gate (Module 15)
        ↓
Filesystem Agent (Module 17)
  ├── PathSecurityService (Normalization, Sandbox Roots, Traversal, Symlink Escapes)
  ├── FilesystemObservationService / FilesystemMutationService
  └── FilesystemBackend Abstraction
        ├── MockFilesystemBackend (Testing & Simulation)
        └── LocalFilesystemBackend (Safe OS Pathlib APIs)
```

## 3. Filesystem Model
Domain entities reflect robust, explicit typing:
- `PathReference`: Tracks original, normalized, resolved paths, path type, and root boundaries.
- `FileMetadata` & `DirectoryMetadata`: Detailed attributes (size, timestamps, extensions, mime-types, symlinks).
- `FileSystemEntry`: Unified entry object for directory listings.
- `FileOperationRequest` & `FileOperationResult`: Lifecycle records tracking operation status (`CREATED` → `VALIDATING` → `AUTHORIZED` → `RUNNING` → `COMPLETED`/`FAILED`/`SIMULATED`/`BLOCKED`).

## 4. Backend Abstraction
All operations depend on the abstract `FilesystemBackend` interface.
- `LocalFilesystemBackend`: Uses standard Python `pathlib`, `os`, `shutil`, `hashlib`, `tempfile` APIs. No shell commands or subprocess calls are used.
- `MockFilesystemBackend`: In-memory thread-safe virtual filesystem for unit testing and simulation.

## 5. Path Security
`PathSecurityService` enforces:
1. Full path resolution via `pathlib.Path.resolve()`.
2. Prevention of directory traversal (`../`, `..\\`, encoded segments).
3. Verification that resolved paths reside within configured `allowed_roots`.
4. Rejection of paths inside `blocked_roots` or system `protected_paths`.

## 6. Sandbox Roots
Sandbox configuration determines valid operating boundaries:
- `MAX_FILESYSTEM_ALLOWED_ROOTS`: Explicit list of directories Max is authorized to access (e.g. workspace, user projects).
- `MAX_FILESYSTEM_READ_ONLY_ROOTS`: Read-only directories.
- `MAX_FILESYSTEM_BLOCKED_ROOTS`: Strictly forbidden directories.

## 7. Protected Paths
System paths are blocked by default:
- Windows: `C:\Windows`, `C:\Program Files`, `C:\Program Files (x86)`, `C:\System32`, `C:\ProgramData`.
- Linux/WSL: `/etc`, `/boot`, `/sys`, `/proc`, `/dev`, `/usr`, `/sbin`.

## 8. Symlink Handling
Before following any symlink or junction point:
- The target is fully resolved via `.resolve()`.
- The resolved target path must remain inside an allowed sandbox root.
- If the target escapes the sandbox root, `SymlinkEscapeError` is raised and execution is blocked.

## 9. File Reading
- Supported content modes: Text (`UTF-8`, `ASCII`, `Latin-1`) and Binary.
- Enforces `MAX_READ_BYTES` (default 10 MB). Oversized files return `truncated=True` or `FileTooLargeError`. Chunked/offset reads supported.

## 10. File Writing
- Atomic write pattern: Writes content to a temporary file in the same directory, flushes disk buffers, and replaces target atomically.
- Default `overwrite=False` prevents accidental data loss.

## 11. Copy / Move / Rename
- `COPY`, `MOVE`, and `RENAME` validate both source and destination paths.
- Authorization must cover both source and destination roots before execution.

## 12. Deletion Safeguards
- Destructive operations (`DELETE_FILE`, `DELETE_DIRECTORY`) require explicit high-risk authorization.
- `DELETE_DIRECTORY` with `recursive=True` requires explicit flag confirmation. Never recursively deletes by default.

## 13. Search Safety
- Recursive directory searching is bounded by `MAX_SEARCH_RESULTS`, `MAX_SEARCH_DEPTH`, and timeouts. Partial results indicate `limit_reached=True`.

## 14. Hashing & Comparison
- File hashing supports `SHA-256` (default), `SHA-512`, and `MD5`.
- `compare_files` compares size, SHA-256 hash, and byte equality without loading entire files into memory.

## 15. Permissions Integration
Maps `FileOperationType` to Module 15 `PermissionAction` (`READ`, `WRITE`, `MODIFY`, `DELETE`) and `RiskLevel` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).

## 16. Risk Levels
- `EXISTS`, `STAT`, `LIST`, `HASH`, `COMPARE`: LOW
- `READ`, `SEARCH`, `CREATE`, `COPY`: MEDIUM
- `WRITE`, `APPEND`, `MOVE`, `RENAME`, `DELETE_FILE`: HIGH
- `DELETE_DIRECTORY` (Recursive): CRITICAL

## 17. Dry-Run Mode
When `MAX_FILESYSTEM_DRY_RUN=True` or parameter `dry_run=True`, operations undergo validation and authorization, then return `SIMULATED` without modifying the filesystem.

## 18. Mock Backend
`MockFilesystemBackend` provides an isolated in-memory filesystem for testing without disk side effects.

## 19. Configuration Options
Configuration keys in `src/max/config/sections.py`:
- `MAX_FILESYSTEM_ENABLED`: Enable/disable subsystem.
- `MAX_FILESYSTEM_DRY_RUN`: Enable global simulation mode.
- `MAX_FILESYSTEM_ALLOWED_ROOTS`: Sandbox allowed directory paths.
- `MAX_FILESYSTEM_MAX_READ_BYTES`: Max bytes per read call.
- `MAX_FILESYSTEM_MAX_SEARCH_RESULTS`: Max search results cap.

## 20. API Endpoints
Base path: `/api/v1/filesystem`
- `GET /status`: Query operational capabilities.
- `POST /exists`, `/stat`, `/list`: Path inspection.
- `POST /read`, `/search`, `/hash`, `/compare`: Read-only queries.
- `POST /create`, `/mkdir`, `/write`, `/append`: State creation & mutation.
- `POST /copy`, `/move`, `/rename`, `/delete`: File/directory operations.
- `POST /operations`, `GET /operations`, `GET /operations/{id}`, `POST /operations/{id}/cancel`: Operations lifecycle tracking.

## 21. Testing Strategy
- Unit tests: Domain models, path security validations, backends, service layer.
- Integration tests: Tool Registry registration and security gate checks.
- E2E tests: TestClient REST API endpoints.

## 22. Manual Smoke Test
1. Set `MAX_FILESYSTEM_DRY_RUN=True`.
2. Send `GET /api/v1/filesystem/status`.
3. Test `POST /api/v1/filesystem/exists` with sample path.
4. Test `POST /api/v1/filesystem/write` with `dry_run=True` -> verify `SIMULATED`.
5. Verify path traversal `POST /api/v1/filesystem/read` with `../../` -> verify `BLOCKED`.

## 23. Security Limitations
- Filesystem Agent cannot bypass OS file permissions or ACLs.
- Executing files (.exe, .sh, .py, .bat) is strictly forbidden in Module 17.

## 24. Future Extensions
- Module 18 (Terminal Agent) will introduce shell/command execution.
- Module 24 (Document Intelligence) will handle document parsing and OCR.
