"""Provider discovery via entry points."""

from __future__ import annotations

from importlib.metadata import entry_points
from typing import TYPE_CHECKING

from amygdala.exceptions import ProviderNotFoundError

if TYPE_CHECKING:
    from amygdala.providers.base import LLMProvider


def get_provider_class(name: str) -> type[LLMProvider]:
    """Look up a provider class by name from entry points."""
    eps = entry_points(group="amygdala.providers")
    for ep in eps:
        if ep.name == name:
            cls = ep.load()
            return cls
    raise ProviderNotFoundError(f"Provider '{name}' not found. Available: {[e.name for e in eps]}")


def list_providers() -> list[str]:
    """List all registered provider names."""
    eps = entry_points(group="amygdala.providers")
    return sorted(ep.name for ep in eps)
