"""Ollama LLM provider."""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator

import httpx

from amygdala.exceptions import ProviderAPIError
from amygdala.providers.base import LLMProvider

OLLAMA_API_URL = "http://localhost:11434/api/chat"


class OllamaProvider(LLMProvider):
    """Ollama local API provider using raw httpx."""

    def __init__(
        self,
        *,
        model_name: str = "llama3",
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self._model = model_name
        self._base_url = (base_url or OLLAMA_API_URL).rstrip("/")

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def model(self) -> str:
        return self._model

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
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    self._base_url,
                    json=payload,
                    timeout=300.0,
                )
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ProviderAPIError(
                    f"Ollama API error {exc.response.status_code}: {exc.response.text}"
                ) from exc
            except httpx.RequestError as exc:
                raise ProviderAPIError(f"Ollama request failed: {exc}") from exc

        data = resp.json()
        return data["message"]["content"]

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
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST",
                    self._base_url,
                    json=payload,
                    timeout=300.0,
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if line:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
            except httpx.HTTPStatusError as exc:
                raise ProviderAPIError(
                    f"Ollama stream error {exc.response.status_code}"
                ) from exc
            except httpx.RequestError as exc:
                raise ProviderAPIError(f"Ollama stream request failed: {exc}") from exc

    async def healthcheck(self) -> bool:
        try:
            # Ollama has a simple health endpoint
            base = self._base_url.replace("/api/chat", "")
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{base}/api/tags", timeout=5.0)
                return resp.status_code == 200
        except Exception:
            return False
