"""Tests for git operations using real temporary repos."""

from __future__ import annotations

from pathlib import Path

import pytest

from amygdala.exceptions import GitError, NotAGitRepoError
from amygdala.git.operations import (
    add_files,
    commit,
    ensure_git_repo,
    get_current_branch,
    get_diff,
    get_diff_names,
    get_file_status,
    get_repo_root,
    get_tracked_files,
    init_repo,
    is_git_repo,
)


@pytest.fixture()
def tmp_git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repo with an initial commit."""
    init_repo(tmp_path)
    # Configure git user for commits
    import subprocess
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path), check=True)
    # Create initial file and commit
    (tmp_path / "README.md").write_text("# Test")
    add_files(tmp_path, ["README.md"])
    commit(tmp_path, "Initial commit")
    return tmp_path


class TestIsGitRepo:
    def test_valid_repo(self, tmp_git_repo: Path):
        assert is_git_repo(tmp_git_repo) is True

    def test_not_a_repo(self, tmp_path: Path):
        assert is_git_repo(tmp_path) is False


class TestEnsureGitRepo:
    def test_valid(self, tmp_git_repo: Path):
        ensure_git_repo(tmp_git_repo)  # should not raise

    def test_invalid(self, tmp_path: Path):
        with pytest.raises(NotAGitRepoError):
            ensure_git_repo(tmp_path)


class TestGetRepoRoot:
    def test_from_root(self, tmp_git_repo: Path):
        root = get_repo_root(tmp_git_repo)
        assert root.resolve() == tmp_git_repo.resolve()

    def test_from_subdir(self, tmp_git_repo: Path):
        subdir = tmp_git_repo / "subdir"
        subdir.mkdir()
        root = get_repo_root(subdir)
        assert root.resolve() == tmp_git_repo.resolve()


class TestGetCurrentBranch:
    def test_default_branch(self, tmp_git_repo: Path):
        branch = get_current_branch(tmp_git_repo)
        # Could be 'main' or 'master' depending on git config
        assert branch in ("main", "master")


class TestGetTrackedFiles:
    def test_lists_tracked_files(self, tmp_git_repo: Path):
        files = get_tracked_files(tmp_git_repo)
        assert "README.md" in files

    def test_includes_new_committed_files(self, tmp_git_repo: Path):
        (tmp_git_repo / "app.py").write_text("print('hello')")
        add_files(tmp_git_repo, ["app.py"])
        commit(tmp_git_repo, "Add app.py")
        files = get_tracked_files(tmp_git_repo)
        assert "app.py" in files


class TestGetDiffNames:
    def test_no_changes(self, tmp_git_repo: Path):
        assert get_diff_names(tmp_git_repo) == []

    def test_unstaged_changes(self, tmp_git_repo: Path):
        (tmp_git_repo / "README.md").write_text("# Updated")
        names = get_diff_names(tmp_git_repo)
        assert "README.md" in names

    def test_staged_changes(self, tmp_git_repo: Path):
        (tmp_git_repo / "README.md").write_text("# Updated")
        add_files(tmp_git_repo, ["README.md"])
        names = get_diff_names(tmp_git_repo, staged=True)
        assert "README.md" in names


class TestGetDiff:
    def test_empty_diff(self, tmp_git_repo: Path):
        diff = get_diff(tmp_git_repo)
        assert diff.strip() == ""

    def test_diff_with_changes(self, tmp_git_repo: Path):
        (tmp_git_repo / "README.md").write_text("# Updated")
        diff = get_diff(tmp_git_repo)
        assert "+# Updated" in diff

    def test_diff_specific_file(self, tmp_git_repo: Path):
        (tmp_git_repo / "README.md").write_text("# Updated")
        (tmp_git_repo / "other.txt").write_text("other")
        add_files(tmp_git_repo, ["other.txt"])
        commit(tmp_git_repo, "Add other")
        (tmp_git_repo / "other.txt").write_text("changed")
        diff = get_diff(tmp_git_repo, file_path="README.md")
        assert "+# Updated" in diff
        assert "changed" not in diff


class TestGetFileStatus:
    def test_clean_repo(self, tmp_git_repo: Path):
        assert get_file_status(tmp_git_repo) == {}

    def test_modified_file(self, tmp_git_repo: Path):
        (tmp_git_repo / "README.md").write_text("# Updated")
        status = get_file_status(tmp_git_repo)
        assert "README.md" in status
        assert "M" in status["README.md"]

    def test_untracked_file(self, tmp_git_repo: Path):
        (tmp_git_repo / "new.txt").write_text("new")
        status = get_file_status(tmp_git_repo)
        assert "new.txt" in status
        assert "?" in status["new.txt"]


class TestInitRepo:
    def test_creates_repo(self, tmp_path: Path):
        init_repo(tmp_path)
        assert is_git_repo(tmp_path)


class TestCommit:
    def test_commit_returns_hash(self, tmp_git_repo: Path):
        (tmp_git_repo / "test.py").write_text("x = 1")
        add_files(tmp_git_repo, ["test.py"])
        sha = commit(tmp_git_repo, "Add test")
        assert len(sha) >= 7  # short hash


class TestGitErrorHandling:
    def test_bad_command(self, tmp_git_repo: Path):
        from amygdala.git.operations import _run
        with pytest.raises(GitError):
            _run(["log", "--invalid-flag-does-not-exist-xyz"], cwd=tmp_git_repo)
