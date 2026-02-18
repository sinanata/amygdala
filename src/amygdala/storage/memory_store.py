"""Read/write .amygdala/memory/*.md files with YAML frontmatter."""

from __future__ import annotations

from pathlib import Path

import yaml

from amygdala.exceptions import MemoryFileNotFoundError
from amygdala.models.memory import MemoryFile, Summary
from amygdala.storage.layout import memory_path_for_file


def write_memory_file(project_root: Path, memory: MemoryFile) -> Path:
    """Write a MemoryFile to disk as YAML frontmatter + Markdown body."""
    path = memory_path_for_file(project_root, memory.relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    latest = memory.latest_summary
    frontmatter: dict = {
        "relative_path": memory.relative_path,
        "language": memory.language,
    }
    if latest:
        frontmatter["summary"] = {
            "granularity": latest.granularity.value,
            "generated_at": latest.generated_at.isoformat(),
            "provider": latest.provider,
            "model": latest.model,
        }
        if latest.token_count is not None:
            frontmatter["summary"]["token_count"] = latest.token_count

    body = latest.content if latest else ""

    content = "---\n"
    content += yaml.dump(frontmatter, default_flow_style=False).rstrip()
    content += "\n---\n\n"
    content += body
    content += "\n"

    path.write_text(content, encoding="utf-8")
    return path


def read_memory_file(project_root: Path, relative_path: str) -> MemoryFile:
    """Read a memory file from disk."""
    from datetime import datetime, timezone
    from amygdala.models.enums import Granularity

    path = memory_path_for_file(project_root, relative_path)
    if not path.exists():
        raise MemoryFileNotFoundError(f"Memory file not found: {path}")

    text = path.read_text(encoding="utf-8")
    frontmatter, body = _parse_frontmatter(text)

    summaries = []
    if body and "summary" in frontmatter:
        sm = frontmatter["summary"]
        summaries.append(Summary(
            content=body,
            granularity=Granularity(sm.get("granularity", "medium")),
            generated_at=datetime.fromisoformat(sm["generated_at"]),
            provider=sm.get("provider", "unknown"),
            model=sm.get("model", "unknown"),
            token_count=sm.get("token_count"),
        ))

    return MemoryFile(
        relative_path=frontmatter.get("relative_path", relative_path),
        language=frontmatter.get("language"),
        summaries=summaries,
    )


def delete_memory_file(project_root: Path, relative_path: str) -> bool:
    """Delete a memory file. Returns True if it existed."""
    path = memory_path_for_file(project_root, relative_path)
    if path.exists():
        path.unlink()
        return True
    return False


def list_memory_files(project_root: Path) -> list[str]:
    """List all relative paths that have memory files."""
    from amygdala.storage.layout import get_memory_dir

    mem_dir = get_memory_dir(project_root)
    if not mem_dir.exists():
        return []

    result = []
    for md_file in mem_dir.rglob("*.md"):
        rel = md_file.relative_to(mem_dir)
        # Remove .md suffix to get the source relative path
        source_rel = str(rel).replace("\\", "/")
        if source_rel.endswith(".md"):
            source_rel = source_rel[:-3]
        result.append(source_rel)
    return sorted(result)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from a markdown file."""
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        fm = {}

    body = parts[2].strip()
    return fm, body
