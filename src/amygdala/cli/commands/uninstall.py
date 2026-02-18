"""amygdala uninstall <adapter> command."""

from __future__ import annotations

from pathlib import Path

import typer

from amygdala.cli.formatting import print_error, print_success
from amygdala.exceptions import AmygdalaError


def uninstall(
    adapter: str = typer.Argument(..., help="Adapter name (e.g. claude-code)"),
    project_dir: Path | None = typer.Option(None, "--dir", help="Project directory"),
) -> None:
    """Uninstall a platform adapter."""
    root = (project_dir or Path.cwd()).resolve()
    try:
        from amygdala.adapters.registry import get_adapter_class
        cls = get_adapter_class(adapter)
        instance = cls()
        instance.uninstall(root)
        print_success(f"Uninstalled adapter: {adapter}")
    except AmygdalaError as exc:
        print_error(str(exc))
        raise typer.Exit(1) from exc
