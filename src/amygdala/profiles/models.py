"""Extension profile data model."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExtensionProfile(BaseModel):
    """A named bundle of extra extensions, language mappings, and exclude patterns."""

    name: str
    description: str = ""
    extensions: frozenset[str] = Field(default_factory=frozenset)
    language_map: dict[str, str] = Field(default_factory=dict)
    exclude_patterns: list[str] = Field(default_factory=list)

    model_config = {"frozen": True}
