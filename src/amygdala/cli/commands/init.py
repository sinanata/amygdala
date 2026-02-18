"""amygdala init command."""

from __future__ import annotations

from pathlib import Path

import typer

from amygdala.cli.formatting import print_error, print_success
from amygdala.core.engine import AmygdalaEngine
from amygdala.exceptions import AmygdalaError


def init(
    provider: str = typer.Option("anthropic", help="LLM provider name"),
    model: str = typer.Option(
        "claude-haiku-4-5-20251001", help="Model identifier",
    ),
    granularity: str = typer.Option(
        "medium", help="Default granularity: simple|medium|high",
    ),
    profile: list[str] | None = typer.Option(
        None, "--profile", "-p",
        help="Extension profile(s) to enable",
    ),
    auto_capture: bool = typer.Option(
        True, help="Enable MCP-driven auto-capture",
    ),
    project_dir: Path | None = typer.Option(
        None, "--dir", help="Project directory",
    ),
) -> None:
    """Initialize Amygdala in a project directory."""
    root = (project_dir or Path.cwd()).resolve()
    try:
        engine = AmygdalaEngine(root)
        config = engine.init(
            provider_name=provider,
            model=model,
            granularity=granularity,
            profiles=profile or None,
            auto_capture=auto_capture,
        )
        print_success(f"Initialized Amygdala in {root}")
        print_success(
            f"Provider: {config.provider.name} / {config.provider.model}"
        )
        if config.profiles:
            print_success(f"Profiles: {', '.join(config.profiles)}")
        if config.auto_capture:
            print_success("Auto-capture: enabled (MCP-driven)")
    except AmygdalaError as exc:
        print_error(str(exc))
        raise typer.Exit(1) from exc
