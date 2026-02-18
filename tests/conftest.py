"""Shared fixtures and Rich coverage bar plugin for the Amygdala test suite."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

import pytest

from amygdala.core.engine import AmygdalaEngine
from amygdala.git.operations import add_files, commit, init_repo
from amygdala.models.config import AmygdalaConfig
from amygdala.models.enums import ProviderName
from amygdala.models.index import IndexFile
from amygdala.models.provider import ProviderConfig
from amygdala.providers.base import LLMProvider

if TYPE_CHECKING:
    from pathlib import Path


class MockLLMProvider(LLMProvider):
    """Reusable mock provider for tests."""

    def __init__(self, response: str = "Mock summary."):
        self._response = response

    @property
    def name(self) -> str:
        return "mock"

    @property
    def model(self) -> str:
        return "mock-model"

    async def generate(self, system_prompt, user_prompt, *, temperature=0.0, max_tokens=4096):
        return self._response

    async def generate_stream(
        self, system_prompt, user_prompt, *, temperature=0.0, max_tokens=4096
    ):
        yield self._response

    async def healthcheck(self) -> bool:
        return True


@pytest.fixture()
def mock_provider() -> MockLLMProvider:
    return MockLLMProvider()


@pytest.fixture()
def sample_config() -> AmygdalaConfig:
    return AmygdalaConfig(
        project_root="/tmp/test-project",
        provider=ProviderConfig(
            name=ProviderName.ANTHROPIC,
            model="claude-haiku-4-5-20251001",
        ),
    )


@pytest.fixture()
def sample_index() -> IndexFile:
    return IndexFile(project_root="/tmp/test-project")


@pytest.fixture()
def tmp_git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repo with an initial commit."""
    init_repo(tmp_path)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=str(tmp_path), check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=str(tmp_path), check=True,
    )
    (tmp_path / "README.md").write_text("# Test Project")
    add_files(tmp_path, ["README.md"])
    commit(tmp_path, "Initial commit")
    return tmp_path


@pytest.fixture()
def tmp_amygdala_project(tmp_git_repo: Path) -> Path:
    """Create a git repo with Amygdala initialized."""
    engine = AmygdalaEngine(tmp_git_repo)
    engine.init(provider_name="anthropic", model="claude-haiku-4-5-20251001")
    return tmp_git_repo


# ── Rich coverage bar plugin ──────────────────────────────────────────


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Render a Rich coverage bar table in terminal summary."""
    try:
        from rich.console import Console
        from rich.table import Table
    except ImportError:
        return

    cov_data = getattr(config, "_cov_total", None)
    if cov_data is None:
        return

    console = Console()
    table = Table(title="Coverage", show_header=True, header_style="bold cyan")
    table.add_column("File")
    table.add_column("Coverage", justify="right")
    table.add_column("Bar", width=30)

    console.print(table)
