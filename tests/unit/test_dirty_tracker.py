"""Tests for dirty tracker with temp git repos."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

import pytest

from amygdala.core.dirty_tracker import get_dirty_files, mark_file_dirty, scan_dirty_files
from amygdala.core.hasher import hash_file
from amygdala.core.index import load_index, save_index, upsert_entry
from amygdala.git.operations import add_files, commit, init_repo
from amygdala.models.enums import FileStatus
from amygdala.models.index import IndexEntry, IndexFile
from amygdala.storage.layout import ensure_layout

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture()
def git_project(tmp_path: Path) -> Path:
    """Create a git project with .amygdala structure and an initial commit."""
    init_repo(tmp_path)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path), check=True)
    ensure_layout(tmp_path)

    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "lib.py").write_text("def foo(): pass")
    add_files(tmp_path, ["main.py", "lib.py"])
    commit(tmp_path, "Initial commit")

    # Create index with entries
    index = IndexFile(project_root=str(tmp_path))
    for name in ["main.py", "lib.py"]:
        upsert_entry(index, IndexEntry(
            relative_path=name,
            content_hash=hash_file(tmp_path / name),
            status=FileStatus.CLEAN,
        ))
    save_index(tmp_path, index)
    return tmp_path


class TestScanDirtyFiles:
    def test_no_changes(self, git_project: Path):
        dirty = scan_dirty_files(git_project)
        assert dirty == []

    def test_modified_file(self, git_project: Path):
        (git_project / "main.py").write_text("print('modified')")
        dirty = scan_dirty_files(git_project)
        assert "main.py" in dirty

    def test_deleted_file(self, git_project: Path):
        (git_project / "lib.py").unlink()
        dirty = scan_dirty_files(git_project)
        assert "lib.py" in dirty

    def test_clean_file_stays_clean(self, git_project: Path):
        dirty = scan_dirty_files(git_project)
        index = load_index(git_project)
        assert index.entries["main.py"].status == FileStatus.CLEAN
        assert dirty == []

    def test_dirty_reverted_becomes_clean(self, git_project: Path):
        # Mark as dirty manually
        index = load_index(git_project)
        index.entries["main.py"].status = FileStatus.DIRTY
        save_index(git_project, index)

        # Scan — file content matches hash, should be clean
        dirty = scan_dirty_files(git_project)
        assert "main.py" not in dirty
        index = load_index(git_project)
        assert index.entries["main.py"].status == FileStatus.CLEAN


class TestMarkFileDirty:
    def test_mark_existing(self, git_project: Path):
        result = mark_file_dirty(git_project, "main.py")
        assert result is True
        index = load_index(git_project)
        assert index.entries["main.py"].status == FileStatus.DIRTY

    def test_mark_nonexistent(self, git_project: Path):
        result = mark_file_dirty(git_project, "nope.py")
        assert result is False


class TestGetDirtyFiles:
    def test_none_dirty(self, git_project: Path):
        assert get_dirty_files(git_project) == []

    def test_some_dirty(self, git_project: Path):
        mark_file_dirty(git_project, "main.py")
        dirty = get_dirty_files(git_project)
        assert "main.py" in dirty
        assert "lib.py" not in dirty
