"""amygdala diff command."""

from __future__ import annotations

from pathlib import Path

import typer

from amygdala.cli.formatting import print_dirty_list, print_error, print_success
from amygdala.core.dirty_tracker import mark_file_dirty, scan_dirty_files
from amygdala.exceptions import AmygdalaError


def diff(
    mark_dirty: str | None = typer.Option(None, "--mark-dirty", help="Mark a file as dirty"),
    project_dir: Path | None = typer.Option(None, "--dir", help="Project directory"),
) -> None:
    """Scan for dirty files or mark a file dirty."""
    root = (project_dir or Path.cwd()).resolve()
    try:
        if mark_dirty:
            result = mark_file_dirty(root, mark_dirty)
            if result:
                print_success(f"Marked {mark_dirty} as dirty")
            else:
                print_error(f"File not in index: {mark_dirty}")
        else:
            dirty = scan_dirty_files(root)
            print_dirty_list(dirty)
    except AmygdalaError as exc:
        print_error(str(exc))
        raise typer.Exit(1) from exc
