"""Adapter discovery via entry points."""

from __future__ import annotations

from importlib.metadata import entry_points
from typing import TYPE_CHECKING

from amygdala.exceptions import AdapterNotFoundError

if TYPE_CHECKING:
    from amygdala.adapters.base import PlatformAdapter


def get_adapter_class(name: str) -> type[PlatformAdapter]:
    """Look up an adapter class by name."""
    eps = entry_points(group="amygdala.adapters")
    for ep in eps:
        if ep.name == name:
            cls = ep.load()
            return cls
    raise AdapterNotFoundError(
        f"Adapter '{name}' not found. Available: {[e.name for e in eps]}"
    )


def list_adapters() -> list[str]:
    """List all registered adapter names."""
    eps = entry_points(group="amygdala.adapters")
    return sorted(ep.name for ep in eps)
