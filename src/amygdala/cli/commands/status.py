"""amygdala status command."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from amygdala.cli.formatting import print_error, print_status_table
from amygdala.core.engine import AmygdalaEngine
from amygdala.exceptions import AmygdalaError


def status(
    as_json: bool = typer.Option(False, "--json", help="Output as JSON"),
    project_dir: Path | None = typer.Option(None, "--dir", help="Project directory"),
) -> None:
    """Show project memory status."""
    root = (project_dir or Path.cwd()).resolve()
    try:
        engine = AmygdalaEngine(root)
        data = engine.status()
        if as_json:
            typer.echo(json.dumps(data, indent=2))
        else:
            print_status_table(data)
    except AmygdalaError as exc:
        print_error(str(exc))
        raise typer.Exit(1) from exc
