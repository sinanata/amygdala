"""amygdala config show/set/get commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from amygdala.cli.formatting import print_config_table, print_error, print_success
from amygdala.core.engine import AmygdalaEngine
from amygdala.exceptions import AmygdalaError

config_app = typer.Typer(name="config", help="Manage configuration.")


@config_app.command("show")
def config_show(
    project_dir: Optional[Path] = typer.Option(None, "--dir", help="Project directory"),
) -> None:
    """Show current configuration."""
    root = (project_dir or Path.cwd()).resolve()
    try:
        engine = AmygdalaEngine(root)
        cfg = engine.load_config()
        print_config_table(cfg.model_dump())
    except AmygdalaError as exc:
        print_error(str(exc))
        raise typer.Exit(1) from exc


@config_app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Config key (dot notation)"),
    project_dir: Optional[Path] = typer.Option(None, "--dir", help="Project directory"),
) -> None:
    """Get a config value."""
    root = (project_dir or Path.cwd()).resolve()
    try:
        engine = AmygdalaEngine(root)
        cfg = engine.load_config()
        data = cfg.model_dump()
        parts = key.split(".")
        val = data
        for part in parts:
            if isinstance(val, dict):
                val = val.get(part)
            else:
                val = None
                break
        if val is not None:
            typer.echo(val)
        else:
            print_error(f"Key not found: {key}")
            raise typer.Exit(1)
    except AmygdalaError as exc:
        print_error(str(exc))
        raise typer.Exit(1) from exc
