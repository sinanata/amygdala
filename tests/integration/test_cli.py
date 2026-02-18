"""Integration tests for the CLI."""

from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from amygdala.cli.app import app
from amygdala.git.operations import add_files, commit, init_repo

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    """Full project setup with git, files, and amygdala init."""
    init_repo(tmp_path)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path), check=True)
    (tmp_path / "main.py").write_text("print('hello world')")
    (tmp_path / "lib.py").write_text("def add(a, b): return a + b")
    (tmp_path / "config.yaml").write_text("key: value")
    add_files(tmp_path, ["main.py", "lib.py", "config.yaml"])
    commit(tmp_path, "Initial commit")
    return tmp_path


@pytest.mark.integration
class TestFullWorkflow:
    def test_init_status_clean(self, project: Path):
        """Test init -> status -> clean workflow."""
        # Init
        result = runner.invoke(app, ["init", "--dir", str(project)])
        assert result.exit_code == 0
        assert "Initialized" in result.output

        # Status as JSON
        result = runner.invoke(app, ["status", "--json", "--dir", str(project)])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["total_tracked"] >= 3
        assert data["dirty_files"] == 0

        # Status as table
        result = runner.invoke(app, ["status", "--dir", str(project)])
        assert result.exit_code == 0

        # Config show
        result = runner.invoke(app, ["config", "show", "--dir", str(project)])
        assert result.exit_code == 0

        # Config get
        result = runner.invoke(app, ["config", "get", "provider.name", "--dir", str(project)])
        assert result.exit_code == 0
        assert "anthropic" in result.output

        # Diff scan
        result = runner.invoke(app, ["diff", "--dir", str(project)])
        assert result.exit_code == 0

        # Clean
        result = runner.invoke(app, ["clean", "--force", "--dir", str(project)])
        assert result.exit_code == 0
        assert not (project / ".amygdala").exists()

    def test_adapter_install_uninstall(self, project: Path):
        """Test adapter install -> status -> uninstall."""
        runner.invoke(app, ["init", "--dir", str(project)])

        result = runner.invoke(app, ["install", "claude-code", "--dir", str(project)])
        assert result.exit_code == 0
        assert "Installed" in result.output
        assert (project / ".amygdala" / "hooks" / "session_start.sh").exists()

        result = runner.invoke(app, ["uninstall", "claude-code", "--dir", str(project)])
        assert result.exit_code == 0
        assert "Uninstalled" in result.output
        assert not (project / ".amygdala" / "hooks").exists()
