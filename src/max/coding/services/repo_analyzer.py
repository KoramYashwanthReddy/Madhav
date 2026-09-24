"""RepositoryAnalyzer service for project type detection and metadata extraction."""

import os
from typing import Any

from max.coding.domain.enums import ProjectType
from max.coding.domain.exceptions import RepositoryNotFoundError
from max.coding.domain.models import DependencyGraph, ProjectMetadata, RepositoryContext
from max.filesystem.container import get_filesystem_container
from max.filesystem.domain.action import FileOperationRequest
from max.filesystem.domain.enums import FileOperationType
from max.filesystem.services.filesystem_service import FilesystemService


class RepositoryAnalyzer:
    """Analyzes repository structure, detects ecosystem project types, and builds project metadata."""

    def __init__(self, filesystem_service: FilesystemService | None = None) -> None:
        if filesystem_service is not None:
            self.fs_service = filesystem_service
        else:
            self.fs_service = get_filesystem_container().filesystem_service

    def detect_project_type(self, root_files: list[str]) -> ProjectType:
        """Detect primary project ecosystem type based on manifest and configuration files."""
        files_lower = {f.lower() for f in root_files}

        if any(f in files_lower for f in ["pyproject.toml", "requirements.txt", "setup.py", "uv.lock"]):
            return ProjectType.PYTHON
        elif any(f in files_lower for f in ["pom.xml", "build.gradle", "build.gradle.kts"]):
            return ProjectType.JAVA
        elif "tsconfig.json" in files_lower:
            return ProjectType.TYPESCRIPT
        elif "package.json" in files_lower:
            return ProjectType.JAVASCRIPT
        elif "cargo.toml" in files_lower:
            return ProjectType.RUST
        elif "go.mod" in files_lower:
            return ProjectType.GO
        elif any(f in files_lower for f in ["cmake-lists.txt", "makefile", "cmakelists.txt"]):
            return ProjectType.C_CPP
        return ProjectType.UNKNOWN

    async def analyze_repository(self, repo_root: str) -> RepositoryContext:
        """Inspect repository filesystem and construct ProjectMetadata and RepositoryContext."""
        if not os.path.exists(repo_root):
            raise RepositoryNotFoundError(repo_root)

        # List repository entries using FilesystemService
        op_req = FileOperationRequest(
            operation_type=FileOperationType.LIST_DIRECTORY,
            source=repo_root,
            owner_id="system",
        )
        op_res = self.fs_service.execute_operation(op_req)
        entries_data = op_res.observed_state.get("entries", [])
        root_filenames: list[str] = []

        for item in entries_data:
            if isinstance(item, dict):
                n = item.get("name", "")
                if n:
                    root_filenames.append(n)
            elif hasattr(item, "name"):
                root_filenames.append(getattr(item, "name"))
            elif isinstance(item, str):
                root_filenames.append(item)

        if not root_filenames and os.path.exists(repo_root):
            try:
                root_filenames = os.listdir(repo_root)
            except Exception:
                pass

        ptype = self.detect_project_type(root_filenames)

        languages: list[str] = []
        frameworks: list[str] = []
        test_framework: str | None = None
        lint_tools: list[str] = []
        type_checker: str | None = None

        if ptype == ProjectType.PYTHON:
            languages.append("Python")
            test_framework = "pytest"
            lint_tools.append("ruff")
            type_checker = "mypy"
            if any("fastapi" in f for f in root_filenames):
                frameworks.append("FastAPI")
        elif ptype in (ProjectType.JAVASCRIPT, ProjectType.TYPESCRIPT):
            languages.append("TypeScript" if ptype == ProjectType.TYPESCRIPT else "JavaScript")
            test_framework = "jest"
            lint_tools.append("eslint")
        elif ptype == ProjectType.RUST:
            languages.append("Rust")
            test_framework = "cargo test"
        elif ptype == ProjectType.GO:
            languages.append("Go")
            test_framework = "go test"

        metadata = ProjectMetadata(
            project_name=os.path.basename(os.path.normpath(repo_root)),
            repo_root=repo_root,
            project_type=ptype,
            languages=languages,
            frameworks=frameworks,
            test_framework=test_framework,
            lint_tools=lint_tools,
            type_checker=type_checker,
            config_files=[f for f in root_filenames if f.endswith((".toml", ".json", ".xml", ".yaml", ".yml"))],
        )

        return RepositoryContext(
            repo_root=repo_root,
            metadata=metadata,
            total_files_count=len(entries_data),
            file_tree=root_filenames,
        )
