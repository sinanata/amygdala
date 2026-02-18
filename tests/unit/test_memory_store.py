"""Tests for memory store (read/write .md files)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from amygdala.exceptions import MemoryFileNotFoundError
from amygdala.models.enums import Granularity
from amygdala.models.memory import MemoryFile, Summary
from amygdala.storage.layout import ensure_layout, memory_path_for_file
from amygdala.storage.memory_store import (
    _parse_frontmatter,
    delete_memory_file,
    list_memory_files,
    read_memory_file,
    write_memory_file,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    ensure_layout(tmp_path)
    return tmp_path


class TestWriteMemoryFile:
    def test_creates_file(self, project: Path):
        mf = MemoryFile(
            relative_path="src/main.py",
            language="python",
            summaries=[
                Summary(
                    content="Main entry point.",
                    granularity=Granularity.SIMPLE,
                    generated_at=datetime.now(UTC),
                    provider="anthropic",
                    model="claude-haiku-4-5-20251001",
                )
            ],
        )
        path = write_memory_file(project, mf)
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "---" in text
        assert "Main entry point." in text
        assert "python" in text

    def test_creates_subdirectories(self, project: Path):
        mf = MemoryFile(
            relative_path="deep/nested/file.py",
            language="python",
        )
        path = write_memory_file(project, mf)
        assert path.exists()

    def test_empty_summaries(self, project: Path):
        mf = MemoryFile(relative_path="empty.py")
        path = write_memory_file(project, mf)
        text = path.read_text(encoding="utf-8")
        assert "---" in text


class TestReadMemoryFile:
    def test_roundtrip(self, project: Path):
        mf = MemoryFile(
            relative_path="src/app.py",
            language="python",
            summaries=[
                Summary(
                    content="App module.",
                    granularity=Granularity.MEDIUM,
                    generated_at=datetime.now(UTC),
                    provider="openai",
                    model="gpt-4o-mini",
                )
            ],
        )
        write_memory_file(project, mf)
        loaded = read_memory_file(project, "src/app.py")
        assert loaded.relative_path == "src/app.py"
        assert loaded.language == "python"

    def test_not_found(self, project: Path):
        with pytest.raises(MemoryFileNotFoundError):
            read_memory_file(project, "nonexistent.py")


class TestDeleteMemoryFile:
    def test_delete_existing(self, project: Path):
        mf = MemoryFile(relative_path="to_delete.py")
        write_memory_file(project, mf)
        assert delete_memory_file(project, "to_delete.py") is True
        assert not memory_path_for_file(project, "to_delete.py").exists()

    def test_delete_nonexistent(self, project: Path):
        assert delete_memory_file(project, "nope.py") is False


class TestListMemoryFiles:
    def test_empty(self, project: Path):
        assert list_memory_files(project) == []

    def test_lists_files(self, project: Path):
        for name in ["a.py", "b.py", "sub/c.py"]:
            write_memory_file(project, MemoryFile(relative_path=name))
        result = list_memory_files(project)
        assert "a.py" in result
        assert "b.py" in result
        assert "sub/c.py" in result

    def test_no_memory_dir(self, tmp_path: Path):
        assert list_memory_files(tmp_path) == []


class TestParseFrontmatter:
    def test_valid(self):
        text = "---\nkey: value\n---\n\nBody text"
        fm, body = _parse_frontmatter(text)
        assert fm["key"] == "value"
        assert body == "Body text"

    def test_no_frontmatter(self):
        text = "Just plain text"
        fm, body = _parse_frontmatter(text)
        assert fm == {}
        assert body == "Just plain text"

    def test_invalid_yaml(self):
        text = "---\n: : : invalid\n---\n\nBody"
        fm, body = _parse_frontmatter(text)
        assert fm == {}

    def test_incomplete_frontmatter(self):
        text = "---\nkey: value"
        fm, body = _parse_frontmatter(text)
        assert fm == {}


class TestLayout:
    def test_ensure_layout(self, tmp_path: Path):
        ensure_layout(tmp_path)
        assert (tmp_path / ".amygdala").exists()
        assert (tmp_path / ".amygdala" / "memory").exists()

    def test_memory_path_for_file(self, tmp_path: Path):
        path = memory_path_for_file(tmp_path, "src/main.py")
        expected = tmp_path / ".amygdala" / "memory" / "src" / "main.py.md"
        assert path == expected
