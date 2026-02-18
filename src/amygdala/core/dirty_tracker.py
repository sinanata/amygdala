"""Git diff dirty detection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from amygdala.core.hasher import hash_file
from amygdala.core.index import get_entry, load_index, save_index, upsert_entry
from amygdala.git.operations import ensure_git_repo
from amygdala.models.enums import FileStatus

if TYPE_CHECKING:
    from pathlib import Path


def scan_dirty_files(project_root: Path) -> list[str]:
    """Find files that have changed since their last capture.

    Compares current file hashes with the index to detect dirty files.
    Returns a list of relative paths that are dirty.
    """
    ensure_git_repo(project_root)
    index = load_index(project_root)
    dirty: list[str] = []

    for rel_path, entry in index.entries.items():
        abs_path = project_root / rel_path
        if not abs_path.exists():
            if entry.status != FileStatus.DELETED:
                entry.status = FileStatus.DELETED
                dirty.append(rel_path)
        else:
            current_hash = hash_file(abs_path)
            if current_hash != entry.content_hash:
                entry.status = FileStatus.DIRTY
                dirty.append(rel_path)
            elif entry.status == FileStatus.DIRTY:
                entry.status = FileStatus.CLEAN

    index.update_counts()
    index.touch_scan()
    save_index(project_root, index)
    return dirty


def mark_file_dirty(project_root: Path, relative_path: str) -> bool:
    """Mark a specific file as dirty in the index.

    Returns True if the file was in the index and marked dirty.
    """
    index = load_index(project_root)
    entry = get_entry(index, relative_path)
    if entry is None:
        return False
    entry.status = FileStatus.DIRTY
    upsert_entry(index, entry)
    save_index(project_root, index)
    return True


def get_dirty_files(project_root: Path) -> list[str]:
    """Return list of files currently marked dirty in the index."""
    index = load_index(project_root)
    return [
        rel for rel, entry in index.entries.items()
        if entry.status == FileStatus.DIRTY
    ]
