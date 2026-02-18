"""Rich tables, coverage bars, and panels for CLI output."""

from __future__ import annotations

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from amygdala.cli.console import console


def print_status_table(status: dict) -> None:
    """Render a Rich status table."""
    table = Table(title="Amygdala Status", show_header=True, header_style="bold cyan")
    table.add_column("Property", style="dim")
    table.add_column("Value")

    table.add_row("Project", status.get("project_root", ""))
    table.add_row("Branch", status.get("branch", ""))
    table.add_row("Provider", f"{status.get('provider', '')} / {status.get('model', '')}")
    table.add_row("Granularity", status.get("granularity", ""))
    table.add_row("Tracked files", str(status.get("total_tracked", 0)))
    table.add_row("Indexed files", str(status.get("total_indexed", 0)))
    table.add_row("Captured files", str(status.get("total_captured", 0)))
    table.add_row("Dirty files", str(status.get("dirty_files", 0)))

    if status.get("last_capture_at"):
        table.add_row("Last capture", status["last_capture_at"])
    if status.get("last_scan_at"):
        table.add_row("Last scan", status["last_scan_at"])

    console.print(table)


def print_dirty_list(dirty: list[str]) -> None:
    """Print a list of dirty files."""
    if not dirty:
        console.print("[green]No dirty files.[/green]")
        return

    table = Table(title=f"Dirty Files ({len(dirty)})", show_header=True, header_style="bold yellow")
    table.add_column("#", style="dim")
    table.add_column("File")

    for i, f in enumerate(dirty, 1):
        table.add_row(str(i), f)

    console.print(table)


def print_capture_result(captured: list[str]) -> None:
    """Print capture results."""
    if not captured:
        console.print("[yellow]No files captured.[/yellow]")
        return

    console.print(f"[green]Captured {len(captured)} file(s):[/green]")
    for f in captured:
        console.print(f"  [dim]•[/dim] {f}")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]{message}[/green]")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]Error: {message}[/red]")


def print_config_table(config_data: dict) -> None:
    """Render config as a table."""
    table = Table(title="Configuration", show_header=True, header_style="bold cyan")
    table.add_column("Key", style="dim")
    table.add_column("Value")

    def _flatten(data: dict, prefix: str = "") -> None:
        for k, v in data.items():
            key = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
            if isinstance(v, dict):
                _flatten(v, key)
            else:
                table.add_row(key, str(v))

    _flatten(config_data)
    console.print(table)
