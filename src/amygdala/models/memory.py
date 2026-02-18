"""Memory file models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from amygdala.models.enums import Granularity


class Summary(BaseModel):
    """A single file summary."""

    content: str
    granularity: Granularity
    generated_at: datetime
    provider: str
    model: str
    token_count: int | None = None


class MemoryFile(BaseModel):
    """Represents a memory .md file with YAML frontmatter."""

    relative_path: str
    language: str | None = None
    summaries: list[Summary] = Field(default_factory=list)

    @property
    def latest_summary(self) -> Summary | None:
        """Return the most recent summary, or None."""
        if not self.summaries:
            return None
        return max(self.summaries, key=lambda s: s.generated_at)
