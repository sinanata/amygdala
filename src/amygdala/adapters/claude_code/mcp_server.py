"""FastMCP server with 5 tools for Claude Code integration."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from amygdala.core.dirty_tracker import get_dirty_files
from amygdala.core.engine import AmygdalaEngine
from amygdala.storage.memory_store import list_memory_files, read_memory_file


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
    def capture_file(file_path: str, granularity: str = "medium") -> str:  # pragma: no cover
        """Capture or update a file's summary."""
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
