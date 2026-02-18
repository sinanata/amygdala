"""Tests for Pydantic models, enums, and related structures."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from amygdala.models.config import AmygdalaConfig
from amygdala.models.enums import (
    AdapterName,
    FileStatus,
    Granularity,
    ProviderName,
)
from amygdala.models.index import IndexEntry, IndexFile
from amygdala.models.memory import MemoryFile, Summary
from amygdala.models.provider import ProviderConfig

# ── Enums ──────────────────────────────────────────────────────────────


class TestGranularity:
    def test_values(self):
        assert Granularity.SIMPLE == "simple"
        assert Granularity.MEDIUM == "medium"
        assert Granularity.HIGH == "high"

    def test_from_string(self):
        assert Granularity("simple") is Granularity.SIMPLE

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            Granularity("nonexistent")


class TestFileStatus:
    def test_values(self):
        assert FileStatus.CLEAN == "clean"
        assert FileStatus.DIRTY == "dirty"
        assert FileStatus.NEW == "new"
        assert FileStatus.DELETED == "deleted"
        assert FileStatus.EXCLUDED == "excluded"

    def test_from_string(self):
        assert FileStatus("dirty") is FileStatus.DIRTY


class TestProviderName:
    def test_values(self):
        assert ProviderName.ANTHROPIC == "anthropic"
        assert ProviderName.OPENAI == "openai"
        assert ProviderName.OLLAMA == "ollama"


class TestAdapterName:
    def test_values(self):
        assert AdapterName.CLAUDE_CODE == "claude-code"
        assert AdapterName.CURSOR == "cursor"
        assert AdapterName.WINDSURF == "windsurf"


# ── ProviderConfig ─────────────────────────────────────────────────────


class TestProviderConfig:
    def test_minimal(self):
        cfg = ProviderConfig(name=ProviderName.ANTHROPIC, model="claude-haiku-4-5-20251001")
        assert cfg.name == ProviderName.ANTHROPIC
        assert cfg.model == "claude-haiku-4-5-20251001"
        assert cfg.api_key is None
        assert cfg.base_url is None
        assert cfg.max_tokens == 4096
        assert cfg.temperature == 0.0

    def test_full(self):
        cfg = ProviderConfig(
            name=ProviderName.OPENAI,
            model="gpt-4o-mini",
            api_key="sk-test",
            base_url="https://api.openai.com/v1",
            max_tokens=2048,
            temperature=0.5,
        )
        assert cfg.api_key == "sk-test"
        assert cfg.base_url == "https://api.openai.com/v1"

    def test_api_key_excluded_from_serialization(self):
        cfg = ProviderConfig(
            name=ProviderName.ANTHROPIC,
            model="claude-haiku-4-5-20251001",
            api_key="secret",
        )
        data = cfg.model_dump()
        assert "api_key" not in data


# ── AmygdalaConfig ─────────────────────────────────────────────────────


class TestAmygdalaConfig:
    def test_defaults(self):
        cfg = AmygdalaConfig(
            project_root="/tmp/proj",
            provider=ProviderConfig(
                name=ProviderName.ANTHROPIC, model="claude-haiku-4-5-20251001"
            ),
        )
        assert cfg.schema_version == 1
        assert cfg.default_granularity == Granularity.MEDIUM
        assert cfg.max_file_size_bytes == 1_000_000
        assert len(cfg.exclude_patterns) > 0

    def test_project_path(self):
        cfg = AmygdalaConfig(
            project_root="/tmp/proj",
            provider=ProviderConfig(
                name=ProviderName.ANTHROPIC, model="claude-haiku-4-5-20251001"
            ),
        )
        assert cfg.project_path == Path("/tmp/proj")

    def test_custom_values(self):
        cfg = AmygdalaConfig(
            project_root="/home/user/project",
            default_granularity=Granularity.HIGH,
            provider=ProviderConfig(name=ProviderName.OLLAMA, model="llama3"),
            exclude_patterns=["*.log"],
            max_file_size_bytes=500_000,
        )
        assert cfg.default_granularity == Granularity.HIGH
        assert cfg.exclude_patterns == ["*.log"]
        assert cfg.max_file_size_bytes == 500_000


# ── IndexEntry / IndexFile ─────────────────────────────────────────────


class TestIndexEntry:
    def test_defaults(self):
        entry = IndexEntry(relative_path="src/main.py", content_hash="abc123")
        assert entry.status == FileStatus.NEW
        assert entry.granularity == Granularity.MEDIUM
        assert entry.memory_path == ""
        assert entry.captured_at is None
        assert entry.file_size_bytes == 0
        assert entry.language is None

    def test_full(self):
        now = datetime.now(UTC)
        entry = IndexEntry(
            relative_path="src/main.py",
            content_hash="abc123",
            status=FileStatus.CLEAN,
            granularity=Granularity.HIGH,
            memory_path="memory/src/main.py.md",
            captured_at=now,
            file_size_bytes=1234,
            language="python",
        )
        assert entry.captured_at == now
        assert entry.language == "python"


class TestIndexFile:
    def test_defaults(self):
        idx = IndexFile()
        assert idx.schema_version == 1
        assert idx.entries == {}
        assert idx.total_files == 0
        assert idx.dirty_files == 0

    def test_update_counts(self):
        idx = IndexFile(
            entries={
                "a.py": IndexEntry(
                    relative_path="a.py", content_hash="h1", status=FileStatus.CLEAN
                ),
                "b.py": IndexEntry(
                    relative_path="b.py", content_hash="h2", status=FileStatus.DIRTY
                ),
                "c.py": IndexEntry(
                    relative_path="c.py", content_hash="h3", status=FileStatus.DIRTY
                ),
            }
        )
        idx.update_counts()
        assert idx.total_files == 3
        assert idx.dirty_files == 2

    def test_touch_scan(self):
        idx = IndexFile()
        assert idx.last_scan_at is None
        idx.touch_scan()
        assert idx.last_scan_at is not None

    def test_touch_capture(self):
        idx = IndexFile()
        assert idx.last_capture_at is None
        idx.touch_capture()
        assert idx.last_capture_at is not None


# ── Summary / MemoryFile ───────────────────────────────────────────────


class TestSummary:
    def test_create(self):
        now = datetime.now(UTC)
        s = Summary(
            content="This file does X.",
            granularity=Granularity.SIMPLE,
            generated_at=now,
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
        )
        assert s.content == "This file does X."
        assert s.token_count is None

    def test_with_token_count(self):
        now = datetime.now(UTC)
        s = Summary(
            content="Detailed summary.",
            granularity=Granularity.HIGH,
            generated_at=now,
            provider="openai",
            model="gpt-4o-mini",
            token_count=150,
        )
        assert s.token_count == 150


class TestMemoryFile:
    def test_empty(self):
        mf = MemoryFile(relative_path="src/foo.py")
        assert mf.latest_summary is None
        assert mf.summaries == []
        assert mf.language is None

    def test_latest_summary(self):
        older = Summary(
            content="Old",
            granularity=Granularity.SIMPLE,
            generated_at=datetime(2025, 1, 1, tzinfo=UTC),
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
        )
        newer = Summary(
            content="New",
            granularity=Granularity.MEDIUM,
            generated_at=datetime(2025, 6, 1, tzinfo=UTC),
            provider="anthropic",
            model="claude-haiku-4-5-20251001",
        )
        mf = MemoryFile(
            relative_path="src/foo.py",
            language="python",
            summaries=[older, newer],
        )
        assert mf.latest_summary is not None
        assert mf.latest_summary.content == "New"
