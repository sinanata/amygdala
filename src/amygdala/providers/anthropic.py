"""Anthropic LLM provider."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import httpx

from amygdala.exceptions import ProviderAPIError, ProviderAuthError
from amygdala.providers.base import LLMProvider

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


class AnthropicProvider(LLMProvider):
    """Anthropic API provider using raw httpx (no SDK dependency required)."""

    def __init__(
        self,
        *,
        model_name: str = "claude-haiku-4-5-20251001",
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self._model = model_name
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._base_url = (base_url or ANTHROPIC_API_URL).rstrip("/")

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def model(self) -> str:
        return self._model

    def _headers(self) -> dict[str, str]:
        if not self._api_key:
            raise ProviderAuthError("ANTHROPIC_API_KEY not set")
        return {
            "x-api-key": self._api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> str:
        payload = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    self._base_url,
                    headers=self._headers(),
                    json=payload,
                    timeout=120.0,
                )
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ProviderAPIError(
                    f"Anthropic API error {exc.response.status_code}: {exc.response.text}"
                ) from exc
            except httpx.RequestError as exc:
                raise ProviderAPIError(f"Anthropic request failed: {exc}") from exc

        data = resp.json()
        return data["content"][0]["text"]

    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        payload = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "stream": True,
        }
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST",
                    self._base_url,
                    headers=self._headers(),
                    json=payload,
                    timeout=120.0,
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            import json
                            data = json.loads(line[6:])
                            if data.get("type") == "content_block_delta":
                                yield data["delta"].get("text", "")
            except httpx.HTTPStatusError as exc:
                raise ProviderAPIError(
                    f"Anthropic stream error {exc.response.status_code}"
                ) from exc
            except httpx.RequestError as exc:
                raise ProviderAPIError(f"Anthropic stream request failed: {exc}") from exc

    async def healthcheck(self) -> bool:
        try:
            self._headers()  # Will raise if no API key
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self._base_url,
                    headers=self._headers(),
                    json={
                        "model": self._model,
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "ping"}],
                    },
                    timeout=10.0,
                )
                return resp.status_code == 200
        except Exception:
            return False
