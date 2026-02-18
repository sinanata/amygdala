"""Tests for Claude Code adapter."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

import pytest

from amygdala.adapters.claude_code.adapter import ClaudeCodeAdapter
from amygdala.core.engine import AmygdalaEngine
from amygdala.git.operations import add_files, commit, init_repo

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture()
def adapter() -> ClaudeCodeAdapter:
    return ClaudeCodeAdapter()


@pytest.fixture()
def amygdala_project(tmp_path: Path) -> Path:
    init_repo(tmp_path)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path), check=True)
    (tmp_path / "main.py").write_text("print('hello')")
    add_files(tmp_path, ["main.py"])
    commit(tmp_path, "Initial commit")
    engine = AmygdalaEngine(tmp_path)
    engine.init()
    return tmp_path


class TestProperties:
    def test_name(self, adapter: ClaudeCodeAdapter):
        assert adapter.name == "claude-code"

    def test_is_available(self, adapter: ClaudeCodeAdapter):
        assert adapter.is_available() is True


class TestInstall:
    def test_creates_hooks(self, adapter: ClaudeCodeAdapter, amygdala_project: Path):
        adapter.install(amygdala_project)
        hooks_dir = amygdala_project / ".amygdala" / "hooks"
        assert hooks_dir.exists()
        assert (hooks_dir / "session_start.sh").exists()
        assert (hooks_dir / "post_tool_use.sh").exists()
        assert (hooks_dir / "claude_hooks.json").exists()


class TestUninstall:
    def test_removes_hooks(self, adapter: ClaudeCodeAdapter, amygdala_project: Path):
        adapter.install(amygdala_project)
        adapter.uninstall(amygdala_project)
        hooks_dir = amygdala_project / ".amygdala" / "hooks"
        assert not hooks_dir.exists()

    def test_uninstall_when_not_installed(
        self, adapter: ClaudeCodeAdapter, amygdala_project: Path
    ):
        adapter.uninstall(amygdala_project)  # Should not raise


class TestStatus:
    def test_not_installed(self, adapter: ClaudeCodeAdapter, amygdala_project: Path):
        status = adapter.status(amygdala_project)
        assert status["installed"] is False

    def test_installed(self, adapter: ClaudeCodeAdapter, amygdala_project: Path):
        adapter.install(amygdala_project)
        status = adapter.status(amygdala_project)
        assert status["installed"] is True
        assert status["session_start_hook"] is True
        assert status["post_tool_use_hook"] is True


class TestGetContextForSession:
    def test_returns_context(self, adapter: ClaudeCodeAdapter, amygdala_project: Path):
        context = adapter.get_context_for_session(amygdala_project)
        assert "Branch:" in context
        assert "Tracked:" in context

    def test_returns_empty_on_error(self, adapter: ClaudeCodeAdapter, tmp_path: Path):
        context = adapter.get_context_for_session(tmp_path)
        assert context == ""


class TestOnFileChanged:
    def test_marks_file_dirty(self, adapter: ClaudeCodeAdapter, amygdala_project: Path):
        # File not in index, so returns silently
        adapter.on_file_changed(amygdala_project, "main.py")
