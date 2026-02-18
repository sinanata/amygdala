"""Prompt template registry."""

from __future__ import annotations

from amygdala.models.enums import Granularity
from amygdala.prompts.simple import SIMPLE_SYSTEM, SIMPLE_USER
from amygdala.prompts.medium import MEDIUM_SYSTEM, MEDIUM_USER
from amygdala.prompts.high import HIGH_SYSTEM, HIGH_USER


_TEMPLATES: dict[Granularity, tuple[str, str]] = {
    Granularity.SIMPLE: (SIMPLE_SYSTEM, SIMPLE_USER),
    Granularity.MEDIUM: (MEDIUM_SYSTEM, MEDIUM_USER),
    Granularity.HIGH: (HIGH_SYSTEM, HIGH_USER),
}


def get_prompts(granularity: Granularity) -> tuple[str, str]:
    """Return (system_prompt, user_prompt_template) for a granularity level."""
    return _TEMPLATES[granularity]


def format_user_prompt(
    granularity: Granularity,
    *,
    file_path: str,
    language: str | None,
    content: str,
) -> str:
    """Format the user prompt with file context."""
    _, template = get_prompts(granularity)
    return template.format(
        file_path=file_path,
        language=language or "unknown",
        content=content,
    )
