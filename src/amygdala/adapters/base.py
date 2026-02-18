"""Abstract platform adapter interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class PlatformAdapter(ABC):
    """Base class for platform adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Adapter name (e.g. 'claude-code')."""
        ...

    @abstractmethod
    def install(self, project_root: Path) -> None:
        """Install the adapter in the project."""
        ...

    @abstractmethod
    def uninstall(self, project_root: Path) -> None:
        """Uninstall the adapter from the project."""
        ...

    @abstractmethod
    def status(self, project_root: Path) -> dict:
        """Get adapter status."""
        ...

    @abstractmethod
    def get_context_for_session(self, project_root: Path) -> str:
        """Build context string for a new session."""
        ...

    @abstractmethod
    def on_file_changed(self, project_root: Path, file_path: str) -> None:
        """Handle a file change notification."""
        ...

    def is_available(self) -> bool:
        """Check if the adapter's target platform is available."""
        return True
