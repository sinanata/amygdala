"""FastMCP server with tools for Claude Code integration."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

from mcp.server.fastmcp import FastMCP

from amygdala.core.dirty_tracker import get_dirty_files
from amygdala.core.engine import AmygdalaEngine
from amygdala.core.resolver import detect_language
from amygdala.storage.memory_store import list_memory_files, read_memory_file

if TYPE_CHECKING:
    from pathlib import Path


def create_mcp_server(project_root: Path) -> FastMCP:
    """Create and configure the MCP server."""
    mcp = FastMCP("amygdala")

    @mcp.tool()
    def get_file_summary(file_path: str) -> str:  # pragma: no cover
        """Retrieve a file's summary from memory."""
        try:
            memory = read_memory_file(project_root, file_path)
            latest = memory.latest_summary
            if latest:
                return latest.content
            return f"No summary found for {file_path}"
        except Exception as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def get_project_overview() -> str:  # pragma: no cover
        """Get project-wide memory status."""
        try:
            engine = AmygdalaEngine(project_root)
            status = engine.status()
            return json.dumps(status, indent=2)
        except Exception as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def list_dirty_files() -> str:  # pragma: no cover
        """List files changed since last capture."""
        try:
            dirty = get_dirty_files(project_root)
            if not dirty:
                return "No dirty files."
            return "\n".join(dirty)
        except Exception as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def capture_file(  # pragma: no cover
        file_path: str,
        granularity: str = "medium",
    ) -> str:
        """Capture or update a file's summary using the configured LLM provider.

        This requires an API key for the configured provider.
        Prefer store_summary() when running inside Claude Code,
        as it uses no API key and no extra cost.
        """
        try:
            from amygdala.models.enums import Granularity
            engine = AmygdalaEngine(project_root)
            result = asyncio.run(engine.capture(
                [file_path],
                granularity=Granularity(granularity),
            ))
            if result:
                return f"Captured: {', '.join(result)}"
            return f"No files captured for {file_path}"
        except Exception as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def read_file_for_capture(file_path: str) -> str:  # pragma: no cover
        """Read a file's content so you can generate a summary for it.

        Returns the file content along with metadata (language, size).
        After reading, generate a concise summary and pass it to
        store_summary() to persist it in Amygdala's memory.
        """
        try:
            abs_path = project_root / file_path
            if not abs_path.exists():
                return f"Error: File not found: {file_path}"

            content = abs_path.read_text(encoding="utf-8", errors="replace")
            language = detect_language(file_path) or "unknown"
            size = abs_path.stat().st_size

            return json.dumps({
                "file_path": file_path,
                "language": language,
                "size_bytes": size,
                "content": content,
            })
        except Exception as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def store_summary(  # pragma: no cover
        file_path: str,
        summary: str,
        granularity: str = "medium",
    ) -> str:
        """Store a summary you have written for a file. No API key needed.

        This is the preferred way to update file memory during a Claude Code
        session. Read the file (or use read_file_for_capture), write a
        concise summary of its purpose and key components, then call this
        tool to persist it. The file will be marked as clean.
        """
        try:
            from amygdala.models.enums import Granularity
            engine = AmygdalaEngine(project_root)
            result = engine.store_summary(
                file_path,
                summary,
                granularity=Granularity(granularity),
            )
            return f"Stored summary for {result}"
        except Exception as exc:
            return f"Error: {exc}"

    @mcp.tool()
    def search_memory(query: str) -> str:  # pragma: no cover
        """Search across all summaries for a query string."""
        try:
            files = list_memory_files(project_root)
            results = []
            for f in files:
                try:
                    memory = read_memory_file(project_root, f)
                    latest = memory.latest_summary
                    if latest and query.lower() in latest.content.lower():
                        results.append(f"{f}: {latest.content[:200]}...")
                except Exception:
                    continue
            if not results:
                return f"No results for '{query}'"
            return "\n\n".join(results)
        except Exception as exc:
            return f"Error: {exc}"

    return mcp
