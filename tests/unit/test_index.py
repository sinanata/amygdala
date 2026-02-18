"""Tests for index manager."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from amygdala.core.index import (
    get_entry,
    load_index,
    remove_entry,
    save_index,
    upsert_entry,
)
from amygdala.exceptions import IndexCorruptedError
from amygdala.models.enums import FileStatus
from amygdala.models.index import IndexEntry, IndexFile
from amygdala.storage.layout import get_index_path

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    """Create a basic project with .amygdala dir."""
    (tmp_path / ".amygdala").mkdir()
    return tmp_path


class TestLoadIndex:
    def test_no_index_file(self, project: Path):
        idx = load_index(project)
        assert isinstance(idx, IndexFile)
        assert idx.entries == {}

    def test_load_valid_index(self, project: Path):
        idx = IndexFile(project_root=str(project))
        upsert_entry(idx, IndexEntry(relative_path="a.py", content_hash="h1"))
        save_index(project, idx)
        loaded = load_index(project)
        assert "a.py" in loaded.entries
        assert loaded.entries["a.py"].content_hash == "h1"

    def test_corrupted_index(self, project: Path):
        path = get_index_path(project)
        path.write_text("not valid json{{{", encoding="utf-8")
        with pytest.raises(IndexCorruptedError):
            load_index(project)


class TestSaveIndex:
    def test_creates_file(self, project: Path):
        idx = IndexFile(project_root=str(project))
        save_index(project, idx)
        path = get_index_path(project)
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["schema_version"] == 1

    def test_creates_parent_dirs(self, tmp_path: Path):
        # No .amygdala dir exists yet
        idx = IndexFile(project_root=str(tmp_path))
        save_index(tmp_path, idx)
        assert get_index_path(tmp_path).exists()


class TestUpsertEntry:
    def test_insert_new(self):
        idx = IndexFile()
        entry = IndexEntry(relative_path="foo.py", content_hash="h1")
        upsert_entry(idx, entry)
        assert "foo.py" in idx.entries
        assert idx.total_files == 1

    def test_update_existing(self):
        idx = IndexFile()
        upsert_entry(idx, IndexEntry(relative_path="foo.py", content_hash="h1"))
        upsert_entry(idx, IndexEntry(relative_path="foo.py", content_hash="h2"))
        assert idx.entries["foo.py"].content_hash == "h2"
        assert idx.total_files == 1

    def test_counts_updated(self):
        idx = IndexFile()
        upsert_entry(idx, IndexEntry(
            relative_path="a.py", content_hash="h1", status=FileStatus.DIRTY
        ))
        upsert_entry(idx, IndexEntry(
            relative_path="b.py", content_hash="h2", status=FileStatus.CLEAN
        ))
        assert idx.total_files == 2
        assert idx.dirty_files == 1


class TestRemoveEntry:
    def test_remove_existing(self):
        idx = IndexFile()
        upsert_entry(idx, IndexEntry(relative_path="foo.py", content_hash="h1"))
        assert remove_entry(idx, "foo.py") is True
        assert "foo.py" not in idx.entries
        assert idx.total_files == 0

    def test_remove_nonexistent(self):
        idx = IndexFile()
        assert remove_entry(idx, "nope.py") is False


class TestGetEntry:
    def test_existing(self):
        idx = IndexFile()
        upsert_entry(idx, IndexEntry(relative_path="foo.py", content_hash="h1"))
        entry = get_entry(idx, "foo.py")
        assert entry is not None
        assert entry.content_hash == "h1"

    def test_nonexistent(self):
        idx = IndexFile()
        assert get_entry(idx, "nope.py") is None
