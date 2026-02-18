"""Google Gemini LLM provider."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

import httpx

from amygdala.exceptions import ProviderAPIError, ProviderAuthError
from amygdala.providers.base import LLMProvider

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(LLMProvider):
    """Google Gemini API provider using raw httpx."""

    def __init__(
        self,
        *,
        model_name: str = "gemini-2.0-flash",
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self._model = model_name
        self._api_key = (
            api_key
            or os.environ.get("GEMINI_API_KEY", "")
            or os.environ.get("GOOGLE_API_KEY", "")
        )
        self._base_url = (base_url or GEMINI_API_URL).rstrip("/")

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def model(self) -> str:
        return self._model

    def _ensure_key(self) -> str:
        if not self._api_key:
            raise ProviderAuthError(
                "GEMINI_API_KEY (or GOOGLE_API_KEY) not set"
            )
        return self._api_key

    def _generate_url(self) -> str:
        return f"{self._base_url}/{self._model}:generateContent"

    def _stream_url(self) -> str:
        return (
            f"{self._base_url}/{self._model}"
            f":streamGenerateContent?alt=sse"
        )

    def _headers(self) -> dict[str, str]:
        return {
            "x-goog-api-key": self._ensure_key(),
            "Content-Type": "application/json",
        }

    @staticmethod
    def _build_payload(
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float,
        max_tokens: int,
    ) -> dict:
        return {
            "system_instruction": {
                "parts": [{"text": system_prompt}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                },
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> str:
        payload = self._build_payload(
            system_prompt, user_prompt,
            temperature=temperature, max_tokens=max_tokens,
        )
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    self._generate_url(),
                    headers=self._headers(),
                    json=payload,
                    timeout=120.0,
                )
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ProviderAPIError(
                    f"Gemini API error {exc.response.status_code}: "
                    f"{exc.response.text}"
                ) from exc
            except httpx.RequestError as exc:
                raise ProviderAPIError(
                    f"Gemini request failed: {exc}"
                ) from exc

        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        payload = self._build_payload(
            system_prompt, user_prompt,
            temperature=temperature, max_tokens=max_tokens,
        )
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST",
                    self._stream_url(),
                    headers=self._headers(),
                    json=payload,
                    timeout=120.0,
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            data = json.loads(line[6:])
                            parts = (
                                data.get("candidates", [{}])[0]
                                .get("content", {})
                                .get("parts", [])
                            )
                            for part in parts:
                                text = part.get("text", "")
                                if text:
                                    yield text
            except httpx.HTTPStatusError as exc:
                raise ProviderAPIError(
                    f"Gemini stream error {exc.response.status_code}"
                ) from exc
            except httpx.RequestError as exc:
                raise ProviderAPIError(
                    f"Gemini stream request failed: {exc}"
                ) from exc

    async def healthcheck(self) -> bool:
        try:
            self._ensure_key()
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self._generate_url(),
                    headers=self._headers(),
                    json=self._build_payload(
                        "You are helpful.", "ping",
                        temperature=0.0, max_tokens=1,
                    ),
                    timeout=10.0,
                )
                return resp.status_code == 200
        except Exception:
            return False
