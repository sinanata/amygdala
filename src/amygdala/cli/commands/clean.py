"""amygdala clean command."""

from __future__ import annotations

import shutil
from pathlib import Path

import typer

from amygdala.cli.formatting import print_error, print_success
from amygdala.storage.layout import get_amygdala_dir


def clean(
    project_dir: Path | None = typer.Option(None, "--dir", help="Project directory"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Remove all Amygdala data from the project."""
    root = (project_dir or Path.cwd()).resolve()
    amygdala_dir = get_amygdala_dir(root)

    if not amygdala_dir.exists():
        print_error("No .amygdala directory found.")
        raise typer.Exit(1)

    if not force:
        confirm = typer.confirm(f"Remove {amygdala_dir}?")
        if not confirm:
            raise typer.Abort()

    shutil.rmtree(amygdala_dir)
    print_success("Cleaned .amygdala directory.")
