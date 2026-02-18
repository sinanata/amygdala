"""Index manager — CRUD on index.json."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from amygdala.exceptions import IndexCorruptedError
from amygdala.models.index import IndexEntry, IndexFile
from amygdala.storage.layout import get_index_path

if TYPE_CHECKING:
    from pathlib import Path


def load_index(project_root: Path) -> IndexFile:
    """Load the index from disk, or return a fresh IndexFile if not found."""
    path = get_index_path(project_root)
    if not path.exists():
        return IndexFile(project_root=str(project_root))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return IndexFile.model_validate(data)
    except (json.JSONDecodeError, Exception) as exc:
        raise IndexCorruptedError(f"Failed to load index: {exc}") from exc


def save_index(project_root: Path, index: IndexFile) -> None:
    """Write the index to disk."""
    path = get_index_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        index.model_dump_json(indent=2),
        encoding="utf-8",
    )


def upsert_entry(index: IndexFile, entry: IndexEntry) -> None:
    """Insert or update an entry in the index."""
    index.entries[entry.relative_path] = entry
    index.update_counts()


def remove_entry(index: IndexFile, relative_path: str) -> bool:
    """Remove an entry from the index. Returns True if it existed."""
    if relative_path in index.entries:
        del index.entries[relative_path]
        index.update_counts()
        return True
    return False


def get_entry(index: IndexFile, relative_path: str) -> IndexEntry | None:
    """Get an entry by relative path, or None."""
    return index.entries.get(relative_path)
