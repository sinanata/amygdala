"""Tests for capture pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from amygdala.core.capture import _validate_file, capture_file, store_file_summary
from amygdala.exceptions import FileTooLargeError, UnsupportedFileError
from amygdala.models.enums import FileStatus, Granularity
from amygdala.providers.base import LLMProvider
from amygdala.storage.layout import ensure_layout

if TYPE_CHECKING:
    from pathlib import Path


class MockProvider(LLMProvider):
    """Mock provider for testing."""

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
def project(tmp_path: Path) -> Path:
    ensure_layout(tmp_path)
    return tmp_path


@pytest.fixture()
def mock_provider() -> MockProvider:
    return MockProvider()


class TestValidateFile:
    def test_nonexistent_file(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            _validate_file(tmp_path / "nope.py", "nope.py", 1_000_000)

    def test_unsupported_extension(self, tmp_path: Path):
        f = tmp_path / "data.xyz"
        f.write_text("data")
        with pytest.raises(UnsupportedFileError, match="xyz"):
            _validate_file(f, "data.xyz", 1_000_000)

    def test_file_too_large(self, tmp_path: Path):
        f = tmp_path / "big.py"
        f.write_text("x" * 100)
        with pytest.raises(FileTooLargeError):
            _validate_file(f, "big.py", 50)

    def test_valid_file(self, tmp_path: Path):
        f = tmp_path / "ok.py"
        f.write_text("print('hi')")
        _validate_file(f, "ok.py", 1_000_000)  # should not raise

    def test_no_extension_is_allowed(self, tmp_path: Path):
        f = tmp_path / "Makefile"
        f.write_text("all: build")
        _validate_file(f, "Makefile", 1_000_000)  # should not raise

    def test_custom_supported_extensions(self, tmp_path: Path):
        f = tmp_path / "scene.unity"
        f.write_text("scene data")
        # Without custom extensions, .unity is unsupported
        with pytest.raises(UnsupportedFileError):
            _validate_file(f, "scene.unity", 1_000_000)
        # With custom extensions that include .unity, it passes
        custom = frozenset({".unity", ".py"})
        _validate_file(f, "scene.unity", 1_000_000, supported_extensions=custom)


class TestCaptureFile:
    async def test_basic_capture(self, project: Path, mock_provider: MockProvider):
        (project / "main.py").write_text("print('hello')")
        entry, memory = await capture_file(
            project_root=project,
            relative_path="main.py",
            provider=mock_provider,
        )
        assert entry.relative_path == "main.py"
        assert entry.status == FileStatus.CLEAN
        assert entry.language == "python"
        assert entry.content_hash
        assert memory.relative_path == "main.py"
        assert memory.latest_summary is not None
        assert memory.latest_summary.content == "Mock summary."

    async def test_capture_with_granularity(self, project: Path, mock_provider: MockProvider):
        (project / "app.js").write_text("const x = 1;")
        entry, _ = await capture_file(
            project_root=project,
            relative_path="app.js",
            provider=mock_provider,
            granularity=Granularity.HIGH,
        )
        assert entry.granularity == Granularity.HIGH

    async def test_capture_writes_memory_file(self, project: Path, mock_provider: MockProvider):
        (project / "lib.py").write_text("def foo(): pass")
        await capture_file(
            project_root=project,
            relative_path="lib.py",
            provider=mock_provider,
        )
        memory_path = project / ".amygdala" / "memory" / "lib.py.md"
        assert memory_path.exists()

    async def test_capture_nested_file(self, project: Path, mock_provider: MockProvider):
        sub = project / "src"
        sub.mkdir()
        (sub / "deep.py").write_text("x = 1")
        entry, _ = await capture_file(
            project_root=project,
            relative_path="src/deep.py",
            provider=mock_provider,
        )
        assert entry.relative_path == "src/deep.py"

    async def test_capture_with_custom_extensions(
        self, project: Path, mock_provider: MockProvider,
    ):
        (project / "scene.unity").write_text("scene data")
        custom_ext = frozenset({".unity", ".py"})
        entry, _ = await capture_file(
            project_root=project,
            relative_path="scene.unity",
            provider=mock_provider,
            supported_extensions=custom_ext,
        )
        assert entry.relative_path == "scene.unity"

    async def test_capture_with_custom_language_map(
        self, project: Path, mock_provider: MockProvider,
    ):
        (project / "effect.shader").write_text("shader code")
        custom_ext = frozenset({".shader"})
        custom_lang = {".shader": "shaderlab"}
        entry, memory = await capture_file(
            project_root=project,
            relative_path="effect.shader",
            provider=mock_provider,
            supported_extensions=custom_ext,
            language_map=custom_lang,
        )
        assert entry.language == "shaderlab"
        assert memory.language == "shaderlab"


class TestStoreFileSummary:
    def test_basic_store(self, project: Path):
        (project / "main.py").write_text("print('hello')")
        entry, memory = store_file_summary(
            project_root=project,
            relative_path="main.py",
            summary_text="Prints hello.",
        )
        assert entry.relative_path == "main.py"
        assert entry.status == FileStatus.CLEAN
        assert entry.language == "python"
        assert entry.content_hash
        assert memory.latest_summary is not None
        assert memory.latest_summary.content == "Prints hello."
        assert memory.latest_summary.provider == "claude-code"
        assert memory.latest_summary.model == "session"

    def test_store_writes_memory_file(self, project: Path):
        (project / "lib.py").write_text("def foo(): pass")
        store_file_summary(
            project_root=project,
            relative_path="lib.py",
            summary_text="A library.",
        )
        memory_path = project / ".amygdala" / "memory" / "lib.py.md"
        assert memory_path.exists()

    def test_store_nonexistent_raises(self, project: Path):
        with pytest.raises(FileNotFoundError):
            store_file_summary(
                project_root=project,
                relative_path="nope.py",
                summary_text="Gone.",
            )

    def test_store_with_custom_language_map(self, project: Path):
        (project / "effect.shader").write_text("shader code")
        entry, memory = store_file_summary(
            project_root=project,
            relative_path="effect.shader",
            summary_text="A shader.",
            language_map={".shader": "shaderlab"},
        )
        assert entry.language == "shaderlab"
        assert memory.language == "shaderlab"

    def test_store_with_granularity(self, project: Path):
        (project / "main.py").write_text("x = 1")
        entry, _ = store_file_summary(
            project_root=project,
            relative_path="main.py",
            summary_text="A variable.",
            granularity=Granularity.HIGH,
        )
        assert entry.granularity == Granularity.HIGH
