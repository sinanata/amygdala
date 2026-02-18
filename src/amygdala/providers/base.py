"""Abstract LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class LLMProvider(ABC):
    """Base class for all LLM providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g. 'anthropic')."""
        ...

    @property
    @abstractmethod
    def model(self) -> str:
        """Model identifier."""
        ...

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> str:
        """Generate a completion."""
        ...

    @abstractmethod
    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Generate a streaming completion."""
        ...
        yield ""  # pragma: no cover

    @abstractmethod
    async def healthcheck(self) -> bool:
        """Check if the provider is reachable."""
        ...
