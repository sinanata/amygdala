"""OpenAI LLM provider."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

import httpx

from amygdala.exceptions import ProviderAPIError, ProviderAuthError
from amygdala.providers.base import LLMProvider

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider(LLMProvider):
    """OpenAI API provider using raw httpx."""

    def __init__(
        self,
        *,
        model_name: str = "gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self._model = model_name
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._base_url = (base_url or OPENAI_API_URL).rstrip("/")

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model(self) -> str:
        return self._model

    def _headers(self) -> dict[str, str]:
        if not self._api_key:
            raise ProviderAuthError("OPENAI_API_KEY not set")
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
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
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
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
                    f"OpenAI API error {exc.response.status_code}: {exc.response.text}"
                ) from exc
            except httpx.RequestError as exc:
                raise ProviderAPIError(f"OpenAI request failed: {exc}") from exc

        data = resp.json()
        return data["choices"][0]["message"]["content"]

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
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
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
                        if line.startswith("data: ") and line != "data: [DONE]":
                            data = json.loads(line[6:])
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
            except httpx.HTTPStatusError as exc:
                raise ProviderAPIError(
                    f"OpenAI stream error {exc.response.status_code}"
                ) from exc
            except httpx.RequestError as exc:
                raise ProviderAPIError(f"OpenAI stream request failed: {exc}") from exc

    async def healthcheck(self) -> bool:
        try:
            self._headers()
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
