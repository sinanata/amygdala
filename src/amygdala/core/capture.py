"""Capture pipeline — file to LLM to summary."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from amygdala.constants import MAX_FILE_SIZE_BYTES, SUPPORTED_EXTENSIONS
from amygdala.core.hasher import hash_file
from amygdala.core.resolver import detect_language, source_to_memory_path
from amygdala.exceptions import FileTooLargeError, UnsupportedFileError
from amygdala.models.enums import FileStatus, Granularity
from amygdala.models.index import IndexEntry
from amygdala.models.memory import MemoryFile, Summary
from amygdala.prompts.templates import format_user_prompt, get_prompts
from amygdala.storage.memory_store import write_memory_file

if TYPE_CHECKING:
    from pathlib import Path

    from amygdala.providers.base import LLMProvider


async def capture_file(
    *,
    project_root: Path,
    relative_path: str,
    provider: LLMProvider,
    granularity: Granularity = Granularity.MEDIUM,
    max_file_size: int = MAX_FILE_SIZE_BYTES,
    supported_extensions: frozenset[str] | None = None,
    language_map: dict[str, str] | None = None,
) -> tuple[IndexEntry, MemoryFile]:
    """Capture a single file: read, validate, send to LLM, store summary.

    Returns the updated IndexEntry and MemoryFile.
    """
    abs_path = project_root / relative_path
    _validate_file(
        abs_path, relative_path, max_file_size,
        supported_extensions=supported_extensions,
    )

    content = abs_path.read_text(encoding="utf-8", errors="replace")
    language = detect_language(relative_path, language_map=language_map)
    content_hash = hash_file(abs_path)

    system_prompt, _ = get_prompts(granularity)
    user_prompt = format_user_prompt(
        granularity,
        file_path=relative_path,
        language=language,
        content=content,
    )

    summary_text = await provider.generate(
        system_prompt, user_prompt,
    )

    now = datetime.now(UTC)
    summary = Summary(
        content=summary_text,
        granularity=granularity,
        generated_at=now,
        provider=provider.name,
        model=provider.model,
    )

    memory = MemoryFile(
        relative_path=relative_path,
        language=language,
        summaries=[summary],
    )
    write_memory_file(project_root, memory)

    entry = IndexEntry(
        relative_path=relative_path,
        content_hash=content_hash,
        status=FileStatus.CLEAN,
        granularity=granularity,
        memory_path=source_to_memory_path(relative_path),
        captured_at=now,
        file_size_bytes=abs_path.stat().st_size,
        language=language,
    )

    return entry, memory


def store_file_summary(
    *,
    project_root: Path,
    relative_path: str,
    summary_text: str,
    granularity: Granularity = Granularity.MEDIUM,
    language_map: dict[str, str] | None = None,
) -> tuple[IndexEntry, MemoryFile]:
    """Store a pre-generated summary without calling an LLM.

    Used when Claude Code (or another external agent) has already
    produced the summary and just needs it persisted to memory.
    """
    abs_path = project_root / relative_path
    if not abs_path.exists():
        raise FileNotFoundError(f"File not found: {relative_path}")

    language = detect_language(relative_path, language_map=language_map)
    content_hash = hash_file(abs_path)

    now = datetime.now(UTC)
    summary = Summary(
        content=summary_text,
        granularity=granularity,
        generated_at=now,
        provider="claude-code",
        model="session",
    )

    memory = MemoryFile(
        relative_path=relative_path,
        language=language,
        summaries=[summary],
    )
    write_memory_file(project_root, memory)

    entry = IndexEntry(
        relative_path=relative_path,
        content_hash=content_hash,
        status=FileStatus.CLEAN,
        granularity=granularity,
        memory_path=source_to_memory_path(relative_path),
        captured_at=now,
        file_size_bytes=abs_path.stat().st_size,
        language=language,
    )

    return entry, memory


def _validate_file(
    abs_path: Path,
    relative_path: str,
    max_size: int,
    *,
    supported_extensions: frozenset[str] | None = None,
) -> None:
    """Validate a file is suitable for capture."""
    if not abs_path.exists():
        raise FileNotFoundError(f"File not found: {relative_path}")

    extensions = supported_extensions if supported_extensions is not None else SUPPORTED_EXTENSIONS
    suffix = abs_path.suffix.lower()
    if suffix and suffix not in extensions:
        raise UnsupportedFileError(
            f"Unsupported file type '{suffix}': {relative_path}"
        )

    size = abs_path.stat().st_size
    if size > max_size:
        raise FileTooLargeError(
            f"File too large ({size} bytes > {max_size}): {relative_path}"
        )
