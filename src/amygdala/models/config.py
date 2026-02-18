"""Project configuration model."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from amygdala.models.enums import Granularity
from amygdala.models.provider import ProviderConfig


class AmygdalaConfig(BaseModel):
    """Root configuration for an Amygdala-managed project."""

    schema_version: int = 1
    project_root: str
    default_granularity: Granularity = Granularity.MEDIUM
    provider: ProviderConfig
    profiles: list[str] = Field(default_factory=list)
    auto_capture: bool = True
    exclude_patterns: list[str] = Field(default_factory=lambda: [
        "*.pyc", "__pycache__", ".git", "node_modules", ".venv",
        "venv", "dist", "build", "*.egg-info",
    ])
    max_file_size_bytes: int = 1_000_000

    @property
    def project_path(self) -> Path:
        return Path(self.project_root)
