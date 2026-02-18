"""Integration tests for the capture pipeline."""

from __future__ import annotations

import subprocess
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from amygdala.core.engine import AmygdalaEngine
from amygdala.core.index import load_index
from amygdala.git.operations import add_files, commit, init_repo
from amygdala.models.enums import FileStatus, Granularity
from amygdala.providers.base import LLMProvider
from amygdala.storage.memory_store import list_memory_files, read_memory_file


class IntegrationMockProvider(LLMProvider):
    """Mock provider for integration tests."""

    def __init__(self):
        self.call_count = 0

    @property
    def name(self) -> str:
        return "mock"

    @property
    def model(self) -> str:
        return "mock-model"

    async def generate(self, system_prompt, user_prompt, *, temperature=0.0, max_tokens=4096):
        self.call_count += 1
        # Return a summary that references the file content
        if "main.py" in user_prompt:
            return "Main entry point that prints hello."
        if "lib.py" in user_prompt:
            return "Library module with utility functions."
        return "Generic file summary."

    async def generate_stream(self, system_prompt, user_prompt, *, temperature=0.0, max_tokens=4096):
        yield await self.generate(system_prompt, user_prompt)

    async def healthcheck(self) -> bool:
        return True


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    init_repo(tmp_path)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path), check=True)
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "lib.py").write_text("def add(a, b): return a + b")
    add_files(tmp_path, ["main.py", "lib.py"])
    commit(tmp_path, "Initial commit")

    engine = AmygdalaEngine(tmp_path)
    engine.init()
    return tmp_path


@pytest.mark.integration
class TestCapturePipeline:
    async def test_capture_specific_files(self, project: Path):
        """Capture specific files and verify index + memory."""
        engine = AmygdalaEngine(project)
        provider = IntegrationMockProvider()

        captured = await engine.capture(["main.py"], provider=provider)
        assert captured == ["main.py"]
        assert provider.call_count == 1

        # Verify index
        index = load_index(project)
        assert "main.py" in index.entries
        assert index.entries["main.py"].status == FileStatus.CLEAN
        assert index.entries["main.py"].language == "python"

        # Verify memory file
        memory = read_memory_file(project, "main.py")
        assert memory.relative_path == "main.py"
        assert memory.latest_summary is not None
        assert "entry point" in memory.latest_summary.content

    async def test_capture_all(self, project: Path):
        """Capture all tracked files."""
        engine = AmygdalaEngine(project)
        provider = IntegrationMockProvider()

        captured = await engine.capture(provider=provider)
        assert "main.py" in captured
        assert "lib.py" in captured
        assert provider.call_count >= 2

        # All files have memory
        memory_files = list_memory_files(project)
        assert "main.py" in memory_files
        assert "lib.py" in memory_files

    async def test_capture_with_granularity(self, project: Path):
        """Capture with different granularity levels."""
        engine = AmygdalaEngine(project)
        provider = IntegrationMockProvider()

        captured = await engine.capture(
            ["main.py"],
            granularity=Granularity.HIGH,
            provider=provider,
        )
        assert captured == ["main.py"]

        index = load_index(project)
        assert index.entries["main.py"].granularity == Granularity.HIGH

    async def test_recapture_dirty_file(self, project: Path):
        """Capture a file, modify it, recapture."""
        engine = AmygdalaEngine(project)
        provider = IntegrationMockProvider()

        # Initial capture
        await engine.capture(["main.py"], provider=provider)

        # Modify the file
        (project / "main.py").write_text("print('modified')")

        # Scan for dirty
        dirty = engine.scan()
        assert "main.py" in dirty

        # Recapture
        await engine.capture(["main.py"], provider=provider)

        index = load_index(project)
        assert index.entries["main.py"].status == FileStatus.CLEAN
