"""amygdala serve command — MCP server."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from amygdala.cli.formatting import print_error, print_success


def serve(  # pragma: no cover
    project_dir: Optional[Path] = typer.Option(None, "--dir", help="Project directory"),
) -> None:
    """Start the MCP server."""
    root = (project_dir or Path.cwd()).resolve()
    try:
        from amygdala.adapters.claude_code.mcp_server import create_mcp_server
        server = create_mcp_server(root)
        print_success(f"Starting MCP server for {root}")
        server.run()
    except Exception as exc:
        print_error(str(exc))
        raise typer.Exit(1) from exc
