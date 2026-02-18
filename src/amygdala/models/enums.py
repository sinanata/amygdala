"""Enumerations for Amygdala."""

from enum import StrEnum


class Granularity(StrEnum):
    """Summary detail level."""

    SIMPLE = "simple"
    MEDIUM = "medium"
    HIGH = "high"


class FileStatus(StrEnum):
    """Tracked file status."""

    CLEAN = "clean"
    DIRTY = "dirty"
    NEW = "new"
    DELETED = "deleted"
    EXCLUDED = "excluded"


class ProviderName(StrEnum):
    """Supported LLM provider names."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"
    GEMINI = "gemini"


class AdapterName(StrEnum):
    """Supported platform adapter names."""

    CLAUDE_CODE = "claude-code"
    CURSOR = "cursor"
    WINDSURF = "windsurf"
