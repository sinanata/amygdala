"""amygdala capture command."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer

from amygdala.cli.formatting import print_capture_result, print_error
from amygdala.core.engine import AmygdalaEngine
from amygdala.exceptions import AmygdalaError
from amygdala.models.enums import Granularity


def capture(
    paths: Optional[list[str]] = typer.Argument(None, help="Files to capture"),
    all_files: bool = typer.Option(False, "--all", help="Capture all tracked files"),
    granularity: Optional[str] = typer.Option(None, "--granularity", "-g", help="Granularity level"),
    project_dir: Optional[Path] = typer.Option(None, "--dir", help="Project directory"),
) -> None:
    """Capture file summaries."""
    root = (project_dir or Path.cwd()).resolve()
    try:
        engine = AmygdalaEngine(root)
        gran = Granularity(granularity) if granularity else None
        target_paths = None if all_files else paths
        captured = asyncio.run(engine.capture(target_paths, granularity=gran))
        print_capture_result(captured)
    except AmygdalaError as exc:
        print_error(str(exc))
        raise typer.Exit(1) from exc
