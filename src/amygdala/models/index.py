"""Index file models."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from amygdala.models.enums import FileStatus, Granularity


class IndexEntry(BaseModel):
    """Tracked file entry in the index."""

    relative_path: str
    content_hash: str
    status: FileStatus = FileStatus.NEW
    granularity: Granularity = Granularity.MEDIUM
    memory_path: str = ""
    captured_at: datetime | None = None
    file_size_bytes: int = 0
    language: str | None = None


class IndexFile(BaseModel):
    """Root index file structure."""

    schema_version: int = 1
    project_root: str = ""
    branch: str = ""
    last_scan_at: datetime | None = None
    last_capture_at: datetime | None = None
    total_files: int = 0
    dirty_files: int = 0
    entries: dict[str, IndexEntry] = Field(default_factory=dict)

    def update_counts(self) -> None:
        """Recompute total_files and dirty_files from entries."""
        self.total_files = len(self.entries)
        self.dirty_files = sum(
            1 for e in self.entries.values() if e.status == FileStatus.DIRTY
        )

    def touch_scan(self) -> None:
        """Update last_scan_at to now."""
        self.last_scan_at = datetime.now(timezone.utc)

    def touch_capture(self) -> None:
        """Update last_capture_at to now."""
        self.last_capture_at = datetime.now(timezone.utc)
