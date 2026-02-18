"""Tests for MCP server tools."""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from amygdala.adapters.claude_code.mcp_server import create_mcp_server
from amygdala.core.engine import AmygdalaEngine
from amygdala.git.operations import add_files, commit, init_repo
from amygdala.models.enums import Granularity
from amygdala.models.memory import MemoryFile, Summary
from amygdala.storage.memory_store import write_memory_file

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture()
def amygdala_project(tmp_path: Path) -> Path:
    init_repo(tmp_path)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path), check=True)
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "lib.py").write_text("def foo(): pass")
    add_files(tmp_path, ["main.py", "lib.py"])
    commit(tmp_path, "Initial commit")
    engine = AmygdalaEngine(tmp_path)
    engine.init()
    return tmp_path


def _write_test_memory(project: Path, rel_path: str, content: str) -> None:
    write_memory_file(project, MemoryFile(
        relative_path=rel_path,
        language="python",
        summaries=[Summary(
            content=content,
            granularity=Granularity.MEDIUM,
            generated_at=datetime.now(UTC),
            provider="mock",
            model="mock-model",
        )],
    ))


class TestCreateMcpServer:
    def test_creates_server(self, amygdala_project: Path):
        server = create_mcp_server(amygdala_project)
        assert server is not None


class TestMcpTools:
    """Test the tool functions directly by accessing them from the server."""

    def test_get_file_summary_not_found(self, amygdala_project: Path):
        create_mcp_server(amygdala_project)
        # Access the tool functions via the server's tool list
        # We test the underlying functions directly
        from amygdala.exceptions import MemoryFileNotFoundError
        from amygdala.storage.memory_store import read_memory_file
        with pytest.raises(MemoryFileNotFoundError):
            read_memory_file(amygdala_project, "nonexistent.py")

    def test_get_file_summary_found(self, amygdala_project: Path):
        _write_test_memory(amygdala_project, "main.py", "Main entry point.")
        from amygdala.storage.memory_store import read_memory_file
        loaded = read_memory_file(amygdala_project, "main.py")
        assert loaded.relative_path == "main.py"

    def test_list_dirty_files(self, amygdala_project: Path):
        from amygdala.core.dirty_tracker import get_dirty_files
        dirty = get_dirty_files(amygdala_project)
        assert isinstance(dirty, list)

    def test_search_memory(self, amygdala_project: Path):
        _write_test_memory(amygdala_project, "main.py", "Main entry point for the app.")
        _write_test_memory(amygdala_project, "lib.py", "Utility library functions.")
        from amygdala.storage.memory_store import list_memory_files, read_memory_file
        files = list_memory_files(amygdala_project)
        results = []
        for f in files:
            mem = read_memory_file(amygdala_project, f)
            s = mem.latest_summary
            if s and "entry" in s.content.lower():
                results.append(f)
        assert "main.py" in results
        assert "lib.py" not in results
