"""amygdala init command."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from amygdala.cli.formatting import print_error, print_success
from amygdala.core.engine import AmygdalaEngine
from amygdala.exceptions import AmygdalaError


def init(
    provider: str = typer.Option("anthropic", help="LLM provider name"),
    model: str = typer.Option("claude-haiku-4-5-20251001", help="Model identifier"),
    granularity: str = typer.Option("medium", help="Default granularity: simple|medium|high"),
    project_dir: Optional[Path] = typer.Option(None, "--dir", help="Project directory"),
) -> None:
    """Initialize Amygdala in a project directory."""
    root = (project_dir or Path.cwd()).resolve()
    try:
        engine = AmygdalaEngine(root)
        config = engine.init(
            provider_name=provider,
            model=model,
            granularity=granularity,
        )
        print_success(f"Initialized Amygdala in {root}")
        print_success(f"Provider: {config.provider.name} / {config.provider.model}")
    except AmygdalaError as exc:
        print_error(str(exc))
        raise typer.Exit(1) from exc
