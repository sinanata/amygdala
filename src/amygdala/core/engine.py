"""AmygdalaEngine — central orchestrator."""

from __future__ import annotations

from pathlib import Path

import tomli_w
import yaml

from amygdala.constants import SCHEMA_VERSION
from amygdala.core.capture import capture_file
from amygdala.core.dirty_tracker import get_dirty_files, scan_dirty_files
from amygdala.core.index import load_index, save_index, upsert_entry
from amygdala.exceptions import ConfigNotFoundError
from amygdala.git.operations import ensure_git_repo, get_current_branch, get_tracked_files
from amygdala.models.config import AmygdalaConfig
from amygdala.models.enums import FileStatus, Granularity, ProviderName
from amygdala.models.index import IndexEntry, IndexFile
from amygdala.models.provider import ProviderConfig
from amygdala.providers.base import LLMProvider
from amygdala.providers.registry import get_provider_class
from amygdala.storage.layout import ensure_layout, get_config_path
from amygdala.storage.memory_store import list_memory_files


class AmygdalaEngine:
    """Central orchestrator for all Amygdala operations."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()

    def init(
        self,
        *,
        provider_name: str = "anthropic",
        model: str = "claude-haiku-4-5-20251001",
        granularity: str = "medium",
        api_key: str | None = None,
    ) -> AmygdalaConfig:
        """Initialize Amygdala in the project."""
        ensure_git_repo(self.project_root)
        ensure_layout(self.project_root)

        config = AmygdalaConfig(
            schema_version=SCHEMA_VERSION,
            project_root=str(self.project_root),
            default_granularity=Granularity(granularity),
            provider=ProviderConfig(
                name=ProviderName(provider_name),
                model=model,
                api_key=api_key,
            ),
        )

        config_path = get_config_path(self.project_root)
        data = config.model_dump(exclude_none=True)
        # Remove api_key from serialized config (it's excluded by Pydantic but ensure)
        if "provider" in data and "api_key" in data["provider"]:
            del data["provider"]["api_key"]
        config_path.write_text(
            tomli_w.dumps(data),
            encoding="utf-8",
        )

        # Create initial index
        branch = get_current_branch(self.project_root)
        index = IndexFile(
            schema_version=SCHEMA_VERSION,
            project_root=str(self.project_root),
            branch=branch,
        )
        save_index(self.project_root, index)

        return config

    def load_config(self) -> AmygdalaConfig:
        """Load configuration from .amygdala/config.toml."""
        config_path = get_config_path(self.project_root)
        if not config_path.exists():
            raise ConfigNotFoundError(
                f"No Amygdala config found at {config_path}. Run 'amygdala init' first."
            )

        import tomllib
        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        return AmygdalaConfig.model_validate(data)

    def status(self) -> dict:
        """Get project memory status."""
        config = self.load_config()
        index = load_index(self.project_root)
        branch = get_current_branch(self.project_root)
        tracked = get_tracked_files(self.project_root)
        memory_files = list_memory_files(self.project_root)
        dirty = get_dirty_files(self.project_root)

        return {
            "project_root": str(self.project_root),
            "branch": branch,
            "provider": config.provider.name,
            "model": config.provider.model,
            "granularity": config.default_granularity,
            "total_tracked": len(tracked),
            "total_indexed": index.total_files,
            "total_captured": len(memory_files),
            "dirty_files": len(dirty),
            "dirty_list": dirty,
            "last_scan_at": str(index.last_scan_at) if index.last_scan_at else None,
            "last_capture_at": str(index.last_capture_at) if index.last_capture_at else None,
        }

    async def capture(
        self,
        paths: list[str] | None = None,
        *,
        granularity: Granularity | None = None,
        provider: LLMProvider | None = None,
    ) -> list[str]:
        """Capture file summaries.

        If paths is None, captures all tracked files.
        Returns list of captured file paths.
        """
        config = self.load_config()
        gran = granularity or config.default_granularity

        if provider is None:
            cls = get_provider_class(config.provider.name)
            provider = cls(
                model_name=config.provider.model,
                api_key=config.provider.api_key,
            )

        if paths is None:
            paths = get_tracked_files(self.project_root)

        index = load_index(self.project_root)
        captured: list[str] = []

        for rel_path in paths:
            abs_path = self.project_root / rel_path
            if not abs_path.exists() or abs_path.is_dir():
                continue
            try:
                entry, _ = await capture_file(
                    project_root=self.project_root,
                    relative_path=rel_path,
                    provider=provider,
                    granularity=gran,
                    max_file_size=config.max_file_size_bytes,
                )
                upsert_entry(index, entry)
                captured.append(rel_path)
            except Exception:
                continue

        index.touch_capture()
        save_index(self.project_root, index)
        return captured

    def scan(self) -> list[str]:
        """Scan for dirty files."""
        return scan_dirty_files(self.project_root)
