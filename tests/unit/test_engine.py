"""Tests for AmygdalaEngine."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

import pytest

from amygdala.core.engine import AmygdalaEngine
from amygdala.exceptions import ConfigNotFoundError, ProfileNotFoundError
from amygdala.git.operations import add_files, commit, init_repo
from amygdala.providers.base import LLMProvider
from amygdala.storage.layout import get_config_path

if TYPE_CHECKING:
    from pathlib import Path


class MockProvider(LLMProvider):
    def __init__(self):
        self.calls: list[str] = []

    @property
    def name(self) -> str:
        return "mock"

    @property
    def model(self) -> str:
        return "mock-model"

    async def generate(self, system_prompt, user_prompt, *, temperature=0.0, max_tokens=4096):
        self.calls.append(user_prompt[:50])
        return "Mock summary for testing."

    async def generate_stream(
        self, system_prompt, user_prompt, *, temperature=0.0, max_tokens=4096
    ):
        yield "Mock"

    async def healthcheck(self) -> bool:
        return True


@pytest.fixture()
def git_project(tmp_path: Path) -> Path:
    init_repo(tmp_path)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path), check=True)
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "README.md").write_text("# Test")
    add_files(tmp_path, ["main.py", "README.md"])
    commit(tmp_path, "Initial commit")
    return tmp_path


class TestInit:
    def test_creates_amygdala_dir(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        engine.init(provider_name="anthropic", model="claude-haiku-4-5-20251001")
        assert (git_project / ".amygdala").exists()
        assert (git_project / ".amygdala" / "memory").exists()
        assert get_config_path(git_project).exists()

    def test_creates_config(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        config = engine.init(provider_name="anthropic", model="claude-haiku-4-5-20251001")
        assert config.provider.name == "anthropic"
        assert config.provider.model == "claude-haiku-4-5-20251001"

    def test_creates_index(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        engine.init()
        from amygdala.core.index import load_index
        index = load_index(git_project)
        assert index.schema_version == 1

    def test_init_with_profiles(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        config = engine.init(profiles=["unity", "python"])
        assert config.profiles == ["unity", "python"]

    def test_init_with_invalid_profile_raises(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        with pytest.raises(ProfileNotFoundError, match="bogus"):
            engine.init(profiles=["bogus"])

    def test_init_profiles_persisted(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        engine.init(profiles=["unity"])
        config = engine.load_config()
        assert config.profiles == ["unity"]

    def test_init_auto_capture_default(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        config = engine.init()
        assert config.auto_capture is True

    def test_init_auto_capture_disabled(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        config = engine.init(auto_capture=False)
        assert config.auto_capture is False

    def test_init_auto_capture_persisted(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        engine.init(auto_capture=False)
        config = engine.load_config()
        assert config.auto_capture is False


class TestLoadConfig:
    def test_no_config_raises(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        with pytest.raises(ConfigNotFoundError):
            engine.load_config()

    def test_load_after_init(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        engine.init(provider_name="anthropic", model="claude-haiku-4-5-20251001")
        config = engine.load_config()
        assert config.provider.name == "anthropic"


class TestStatus:
    def test_status_after_init(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        engine.init()
        status = engine.status()
        assert "branch" in status
        assert status["total_tracked"] >= 2  # main.py, README.md
        assert status["total_indexed"] == 0
        assert status["dirty_files"] == 0
        assert status["profiles"] == []
        assert status["auto_capture"] is True

    def test_status_with_profiles(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        engine.init(profiles=["unity"])
        status = engine.status()
        assert status["profiles"] == ["unity"]

    def test_status_auto_capture_disabled(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        engine.init(auto_capture=False)
        status = engine.status()
        assert status["auto_capture"] is False


class TestCapture:
    async def test_capture_specific_files(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        engine.init()
        provider = MockProvider()
        captured = await engine.capture(["main.py"], provider=provider)
        assert "main.py" in captured
        assert len(provider.calls) == 1

    async def test_capture_all(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        engine.init()
        provider = MockProvider()
        captured = await engine.capture(provider=provider)
        assert len(captured) >= 2  # main.py, README.md

    async def test_capture_skips_missing_files(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        engine.init()
        provider = MockProvider()
        captured = await engine.capture(["nonexistent.py"], provider=provider)
        assert captured == []

    async def test_capture_updates_index(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        engine.init()
        provider = MockProvider()
        await engine.capture(["main.py"], provider=provider)
        from amygdala.core.index import load_index
        index = load_index(git_project)
        assert "main.py" in index.entries

    async def test_capture_with_profile_accepts_extra_extensions(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        engine.init(profiles=["unity"])
        # Create a .shader file and add to git
        (git_project / "test.shader").write_text("Shader \"Test\" {}")
        from amygdala.git.operations import add_files, commit
        add_files(git_project, ["test.shader"])
        commit(git_project, "Add shader")
        provider = MockProvider()
        captured = await engine.capture(["test.shader"], provider=provider)
        assert "test.shader" in captured


class TestStoreSummary:
    def test_store_summary_basic(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        engine.init()
        result = engine.store_summary("main.py", "Prints hello.")
        assert result == "main.py"

    def test_store_summary_updates_index(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        engine.init()
        engine.store_summary("main.py", "Prints hello.")
        from amygdala.core.index import load_index
        index = load_index(git_project)
        assert "main.py" in index.entries
        assert index.entries["main.py"].status.value == "clean"

    def test_store_summary_writes_memory(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        engine.init()
        engine.store_summary("main.py", "Prints hello.")
        memory_path = git_project / ".amygdala" / "memory" / "main.py.md"
        assert memory_path.exists()
        content = memory_path.read_text()
        assert "Prints hello." in content

    def test_store_summary_nonexistent_raises(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        engine.init()
        with pytest.raises(FileNotFoundError):
            engine.store_summary("nonexistent.py", "Gone.")


class TestScan:
    def test_scan_no_changes(self, git_project: Path):
        engine = AmygdalaEngine(git_project)
        engine.init()
        dirty = engine.scan()
        assert dirty == []
