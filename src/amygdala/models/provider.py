"""Provider configuration model."""

from __future__ import annotations

from pydantic import BaseModel, Field

from amygdala.models.enums import ProviderName


class ProviderConfig(BaseModel):
    """Configuration for an LLM provider."""

    name: ProviderName
    model: str
    api_key: str | None = Field(default=None, exclude=True)
    base_url: str | None = None
    max_tokens: int = 4096
    temperature: float = 0.0
