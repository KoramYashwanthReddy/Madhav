"""CodeSearchService for reading files, symbol extraction, and text search."""

import os
import re

from max.coding.domain.enums import SymbolType
from max.coding.domain.exceptions import CodingAgentError
from max.coding.domain.models import CodeSymbol
from max.coding.security.prompt_injection import CodeSecurityEnforcer
from max.filesystem.container import get_filesystem_container
from max.filesystem.domain.action import FileOperationRequest
from max.filesystem.domain.enums import FileOperationStatus, FileOperationType
from max.filesystem.services.filesystem_service import FilesystemService


class CodeSearchService:
    """Provides bounded code reading, symbol parsing, and text search capabilities."""

    def __init__(self, filesystem_service: FilesystemService | None = None) -> None:
        if filesystem_service is not None:
            self.fs_service = filesystem_service
        else:
            self.fs_service = get_filesystem_container().filesystem_service

    async def read_file(
        self,
        repo_root: str,
        relative_path: str,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> str:
        """Read code file content through FilesystemService with security validation."""
        full_path = os.path.join(repo_root, relative_path)
        CodeSecurityEnforcer.validate_file_path(full_path)

        text = ""
        try:
            req = FileOperationRequest(
                operation_type=FileOperationType.READ_FILE,
                source=full_path,
                owner_id="system",
            )
            res = self.fs_service.execute_operation(req)
            if res.status != FileOperationStatus.FAILED:
                text = res.observed_state.get("content", "")
                if isinstance(text, bytes):
                    text = text.decode("utf-8", errors="replace")
        except Exception:
            pass

        if not text and os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()

        if start_line or end_line:
            lines = text.splitlines()
            s_idx = max(0, (start_line or 1) - 1)
            e_idx = end_line if end_line else len(lines)
            text = "\n".join(lines[s_idx:e_idx])

        return text

    async def search_code(
        self, repo_root: str, query: str, pattern: str = "*"
    ) -> list[dict[str, str]]:
        """Search code files for matching text queries."""
        req = FileOperationRequest(
            operation_type=FileOperationType.SEARCH_FILES,
            source=repo_root,
            owner_id="system",
            parameters={"query": query, "pattern": pattern},
        )
        res = self.fs_service.execute_operation(req)
        matches: list[dict[str, str]] = []

        if res.status == FileOperationStatus.COMPLETED and "matches" in res.observed_state:
            for item in res.observed_state["matches"]:
                path = item.get("path", "") if isinstance(item, dict) else str(item)
                rel_path = os.path.relpath(path, repo_root)

                # Ignore protected path matches
                try:
                    CodeSecurityEnforcer.validate_file_path(rel_path)
                    matches.append(
                        {
                            "file_path": rel_path,
                            "match": os.path.basename(path),
                        }
                    )
                except Exception:
                    continue

        return matches

    def extract_symbols_from_text(self, relative_path: str, content: str) -> list[CodeSymbol]:
        """Extract top-level symbols (classes, functions) from Python or JS source code."""
        symbols: list[CodeSymbol] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            # Class match
            m_cls = re.match(r"^class\s+([A-Za-z0-9_]+)", stripped)
            if m_cls:
                symbols.append(
                    CodeSymbol(
                        name=m_cls.group(1),
                        symbol_type=SymbolType.CLASS,
                        file_path=relative_path,
                        line_number=idx,
                    )
                )
                continue

            # Function / method match
            m_def = re.match(r"^(?:async\s+)?def\s+([A-Za-z0-9_]+)", stripped)
            if m_def:
                symbols.append(
                    CodeSymbol(
                        name=m_def.group(1),
                        symbol_type=SymbolType.FUNCTION if not line.startswith(" ") else SymbolType.METHOD,
                        file_path=relative_path,
                        line_number=idx,
                    )
                )

        return symbols
