"""AmygdalaEngine — central orchestrator."""

from __future__ import annotations

from typing import TYPE_CHECKING

import tomli_w

from amygdala.constants import SCHEMA_VERSION
from amygdala.core.capture import capture_file, store_file_summary
from amygdala.core.dirty_tracker import get_dirty_files, scan_dirty_files
from amygdala.core.index import load_index, save_index, upsert_entry
from amygdala.exceptions import ConfigNotFoundError
from amygdala.git.operations import ensure_git_repo, get_current_branch, get_tracked_files
from amygdala.models.config import AmygdalaConfig
from amygdala.models.enums import Granularity, ProviderName
from amygdala.models.index import IndexFile
from amygdala.models.provider import ProviderConfig
from amygdala.profiles.registry import (
    get_profile,
    resolve_extensions,
    resolve_language_map,
)
from amygdala.providers.registry import get_provider_class
from amygdala.storage.layout import ensure_layout, get_config_path
from amygdala.storage.memory_store import list_memory_files

if TYPE_CHECKING:
    from pathlib import Path

    from amygdala.providers.base import LLMProvider


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
        profiles: list[str] | None = None,
        auto_capture: bool = True,
    ) -> AmygdalaConfig:
        """Initialize Amygdala in the project."""
        ensure_git_repo(self.project_root)
        ensure_layout(self.project_root)

        # Validate profile names early
        validated_profiles: list[str] = []
        if profiles:
            for name in profiles:
                get_profile(name)  # raises ProfileNotFoundError
                validated_profiles.append(name)

        config = AmygdalaConfig(
            schema_version=SCHEMA_VERSION,
            project_root=str(self.project_root),
            default_granularity=Granularity(granularity),
            provider=ProviderConfig(
                name=ProviderName(provider_name),
                model=model,
                api_key=api_key,
            ),
            profiles=validated_profiles,
            auto_capture=auto_capture,
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

        result: dict = {
            "project_root": str(self.project_root),
            "branch": branch,
            "provider": config.provider.name,
            "model": config.provider.model,
            "granularity": config.default_granularity,
            "profiles": config.profiles,
            "auto_capture": config.auto_capture,
            "total_tracked": len(tracked),
            "total_indexed": index.total_files,
            "total_captured": len(memory_files),
            "dirty_files": len(dirty),
            "dirty_list": dirty,
            "last_scan_at": str(index.last_scan_at) if index.last_scan_at else None,
            "last_capture_at": (
                str(index.last_capture_at) if index.last_capture_at else None
            ),
        }

        if config.auto_capture and dirty:
            result["auto_capture_hint"] = (
                f"{len(dirty)} file(s) have stale summaries: "
                f"{', '.join(dirty[:10])}"
                f"{'...' if len(dirty) > 10 else ''}. "
                "Use the store_summary MCP tool to refresh each file's memory. "
                "Read the file, write a concise summary, "
                "then call store_summary(file_path, summary)."
            )

        return result

    def store_summary(
        self,
        relative_path: str,
        summary_text: str,
        *,
        granularity: Granularity | None = None,
    ) -> str:
        """Store a pre-generated summary (no LLM call).

        Used by MCP tools when Claude Code itself generates the summary.
        Returns the relative path on success.
        """
        config = self.load_config()
        gran = granularity or config.default_granularity

        effective_language_map: dict[str, str] | None = None
        if config.profiles:
            effective_language_map = resolve_language_map(config.profiles)

        entry, _ = store_file_summary(
            project_root=self.project_root,
            relative_path=relative_path,
            summary_text=summary_text,
            granularity=gran,
            language_map=effective_language_map,
        )

        index = load_index(self.project_root)
        upsert_entry(index, entry)
        index.touch_capture()
        save_index(self.project_root, index)

        return relative_path

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

        # Resolve profile-aware extensions and language map
        effective_extensions: frozenset[str] | None = None
        effective_language_map: dict[str, str] | None = None
        if config.profiles:
            effective_extensions = resolve_extensions(config.profiles)
            effective_language_map = resolve_language_map(config.profiles)

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
                    supported_extensions=effective_extensions,
                    language_map=effective_language_map,
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
