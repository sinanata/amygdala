"""Integration tests for git operations."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

import pytest

from amygdala.core.dirty_tracker import scan_dirty_files
from amygdala.core.engine import AmygdalaEngine
from amygdala.core.hasher import hash_file
from amygdala.core.index import load_index, save_index, upsert_entry
from amygdala.git.operations import (
    add_files,
    commit,
    get_current_branch,
    get_diff,
    get_diff_names,
    get_file_status,
    get_tracked_files,
    init_repo,
)
from amygdala.models.enums import FileStatus
from amygdala.models.index import IndexEntry

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    init_repo(tmp_path)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path), check=True)
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "lib.py").write_text("import os")
    add_files(tmp_path, ["main.py", "lib.py"])
    commit(tmp_path, "Initial commit")
    return tmp_path


@pytest.mark.integration
class TestGitIntegration:
    def test_full_git_workflow(self, project: Path):
        """Test git operations work together."""
        # Verify initial state
        branch = get_current_branch(project)
        assert branch in ("main", "master")

        tracked = get_tracked_files(project)
        assert "main.py" in tracked
        assert "lib.py" in tracked

        # Modify a file
        (project / "main.py").write_text("print('modified')")
        status = get_file_status(project)
        assert "main.py" in status

        # Check diff
        diff_names = get_diff_names(project)
        assert "main.py" in diff_names

        diff_content = get_diff(project)
        assert "+print('modified')" in diff_content

        # Stage and commit
        add_files(project, ["main.py"])
        staged_names = get_diff_names(project, staged=True)
        assert "main.py" in staged_names

        sha = commit(project, "Update main.py")
        assert len(sha) >= 7

    def test_dirty_tracking_integration(self, project: Path):
        """Test dirty tracking with real git operations."""
        engine = AmygdalaEngine(project)
        engine.init()

        # Create index entries for files
        index = load_index(project)
        for name in ["main.py", "lib.py"]:
            upsert_entry(index, IndexEntry(
                relative_path=name,
                content_hash=hash_file(project / name),
                status=FileStatus.CLEAN,
            ))
        save_index(project, index)

        # No dirty files initially
        dirty = scan_dirty_files(project)
        assert dirty == []

        # Modify a file
        (project / "main.py").write_text("print('changed')")
        dirty = scan_dirty_files(project)
        assert "main.py" in dirty

        # Verify index was updated
        index = load_index(project)
        assert index.entries["main.py"].status == FileStatus.DIRTY
        assert index.dirty_files == 1
