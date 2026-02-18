"""Parse git diff output into structured data."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DiffHunk:
    """A single hunk from a diff."""

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[str] = field(default_factory=list)


@dataclass
class FileDiff:
    """Parsed diff for a single file."""

    path: str
    old_path: str | None = None
    is_new: bool = False
    is_deleted: bool = False
    is_renamed: bool = False
    hunks: list[DiffHunk] = field(default_factory=list)

    @property
    def added_lines(self) -> int:
        return sum(1 for h in self.hunks for line in h.lines if line.startswith("+"))

    @property
    def removed_lines(self) -> int:
        return sum(1 for h in self.hunks for line in h.lines if line.startswith("-"))


def parse_diff(raw_diff: str) -> list[FileDiff]:
    """Parse raw git diff output into a list of FileDiff objects."""
    if not raw_diff.strip():
        return []

    file_diffs: list[FileDiff] = []
    current_file: FileDiff | None = None
    current_hunk: DiffHunk | None = None

    for line in raw_diff.splitlines():
        if line.startswith("diff --git"):
            # New file diff
            parts = line.split(" b/", 1)
            path = parts[1] if len(parts) > 1 else ""
            current_file = FileDiff(path=path)
            current_hunk = None
            file_diffs.append(current_file)

        elif line.startswith("new file"):
            if current_file:
                current_file.is_new = True

        elif line.startswith("deleted file"):
            if current_file:
                current_file.is_deleted = True

        elif line.startswith("rename from"):
            if current_file:
                current_file.is_renamed = True
                current_file.old_path = line.split("rename from ", 1)[1]

        elif line.startswith("@@"):
            if current_file:
                hunk = _parse_hunk_header(line)
                if hunk:
                    current_hunk = hunk
                    current_file.hunks.append(current_hunk)

        elif current_hunk is not None and (
            line.startswith("+") or line.startswith("-") or line.startswith(" ")
        ):
            current_hunk.lines.append(line)

    return file_diffs


def _parse_hunk_header(line: str) -> DiffHunk | None:
    """Parse a @@ hunk header into a DiffHunk."""
    # Format: @@ -old_start,old_count +new_start,new_count @@
    try:
        parts = line.split("@@")[1].strip().split()
        old_part = parts[0]  # e.g. -1,3
        new_part = parts[1]  # e.g. +1,5

        old_start, old_count = _parse_range(old_part.lstrip("-"))
        new_start, new_count = _parse_range(new_part.lstrip("+"))

        return DiffHunk(
            old_start=old_start,
            old_count=old_count,
            new_start=new_start,
            new_count=new_count,
        )
    except (IndexError, ValueError):
        return None


def _parse_range(range_str: str) -> tuple[int, int]:
    """Parse '1,3' or '1' into (start, count)."""
    if "," in range_str:
        start, count = range_str.split(",", 1)
        return int(start), int(count)
    return int(range_str), 1
