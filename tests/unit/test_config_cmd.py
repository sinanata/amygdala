"""Tests for CLI commands using Typer test client."""

from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from amygdala.cli.app import app
from amygdala.core.engine import AmygdalaEngine
from amygdala.git.operations import add_files, commit, init_repo

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()


@pytest.fixture()
def git_project(tmp_path: Path) -> Path:
    init_repo(tmp_path)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path), check=True)
    (tmp_path / "main.py").write_text("print('hello')")
    add_files(tmp_path, ["main.py"])
    commit(tmp_path, "Initial commit")
    return tmp_path


@pytest.fixture()
def amygdala_project(git_project: Path) -> Path:
    engine = AmygdalaEngine(git_project)
    engine.init()
    return git_project


class TestInitCommand:
    def test_init_success(self, git_project: Path):
        result = runner.invoke(app, ["init", "--dir", str(git_project)])
        assert result.exit_code == 0
        assert "Initialized" in result.output

    def test_init_with_options(self, git_project: Path):
        result = runner.invoke(app, [
            "init",
            "--provider", "anthropic",
            "--model", "claude-haiku-4-5-20251001",
            "--granularity", "high",
            "--dir", str(git_project),
        ])
        assert result.exit_code == 0

    def test_init_not_git_repo(self, tmp_path: Path):
        result = runner.invoke(app, ["init", "--dir", str(tmp_path)])
        assert result.exit_code == 1


class TestStatusCommand:
    def test_status_table(self, amygdala_project: Path):
        result = runner.invoke(app, ["status", "--dir", str(amygdala_project)])
        assert result.exit_code == 0

    def test_status_json(self, amygdala_project: Path):
        result = runner.invoke(app, ["status", "--json", "--dir", str(amygdala_project)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "branch" in data

    def test_status_no_init(self, git_project: Path):
        result = runner.invoke(app, ["status", "--dir", str(git_project)])
        assert result.exit_code == 1


class TestDiffCommand:
    def test_diff_scan(self, amygdala_project: Path):
        result = runner.invoke(app, ["diff", "--dir", str(amygdala_project)])
        assert result.exit_code == 0

    def test_diff_mark_dirty_not_in_index(self, amygdala_project: Path):
        result = runner.invoke(app, [
            "diff", "--mark-dirty", "nonexistent.py", "--dir", str(amygdala_project),
        ])
        assert result.exit_code == 0  # Prints error message but doesn't exit 1
        assert "not in index" in result.output


class TestConfigCommand:
    def test_config_show(self, amygdala_project: Path):
        result = runner.invoke(app, ["config", "show", "--dir", str(amygdala_project)])
        assert result.exit_code == 0

    def test_config_get(self, amygdala_project: Path):
        result = runner.invoke(
            app, ["config", "get", "schema_version", "--dir", str(amygdala_project)]
        )
        assert result.exit_code == 0
        assert "1" in result.output

    def test_config_get_nested(self, amygdala_project: Path):
        result = runner.invoke(
            app, ["config", "get", "provider.name", "--dir", str(amygdala_project)]
        )
        assert result.exit_code == 0
        assert "anthropic" in result.output

    def test_config_get_missing_key(self, amygdala_project: Path):
        result = runner.invoke(
            app, ["config", "get", "nonexistent", "--dir", str(amygdala_project)]
        )
        assert result.exit_code == 1


class TestCleanCommand:
    def test_clean_with_force(self, amygdala_project: Path):
        assert (amygdala_project / ".amygdala").exists()
        result = runner.invoke(app, ["clean", "--force", "--dir", str(amygdala_project)])
        assert result.exit_code == 0
        assert not (amygdala_project / ".amygdala").exists()

    def test_clean_no_amygdala_dir(self, git_project: Path):
        result = runner.invoke(app, ["clean", "--dir", str(git_project)])
        assert result.exit_code == 1

    def test_clean_abort(self, amygdala_project: Path):
        runner.invoke(app, ["clean", "--dir", str(amygdala_project)], input="n\n")
        assert (amygdala_project / ".amygdala").exists()


class TestNoArgsShowsHelp:
    def test_no_args(self):
        result = runner.invoke(app, [])
        # Typer no_args_is_help exits with code 0 or 2
        assert result.exit_code in (0, 2)
        assert "Usage" in result.output or "amygdala" in result.output
