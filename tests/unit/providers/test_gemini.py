"""Tests for Gemini provider using respx mocks."""

from __future__ import annotations

import httpx
import pytest
import respx

from amygdala.exceptions import ProviderAPIError, ProviderAuthError
from amygdala.providers.gemini import GEMINI_API_URL, GeminiProvider

MODEL = "gemini-2.0-flash"
GENERATE_URL = f"{GEMINI_API_URL}/{MODEL}:generateContent"
STREAM_URL = f"{GEMINI_API_URL}/{MODEL}:streamGenerateContent"


@pytest.fixture()
def provider() -> GeminiProvider:
    return GeminiProvider(model_name=MODEL, api_key="test-key")


@pytest.fixture()
def provider_no_key() -> GeminiProvider:
    return GeminiProvider(model_name=MODEL, api_key="")


class TestGeminiProperties:
    def test_name(self, provider: GeminiProvider):
        assert provider.name == "gemini"

    def test_model(self, provider: GeminiProvider):
        assert provider.model == MODEL


class TestGenerate:
    @respx.mock
    async def test_success(self, provider: GeminiProvider):
        respx.post(GENERATE_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "candidates": [
                        {
                            "content": {
                                "parts": [{"text": "Hello from Gemini"}],
                                "role": "model",
                            }
                        }
                    ]
                },
            )
        )
        result = await provider.generate("system", "user prompt")
        assert result == "Hello from Gemini"

    @respx.mock
    async def test_api_error(self, provider: GeminiProvider):
        respx.post(GENERATE_URL).mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        with pytest.raises(ProviderAPIError, match="500"):
            await provider.generate("system", "prompt")

    @respx.mock
    async def test_request_error(self, provider: GeminiProvider):
        respx.post(GENERATE_URL).mock(
            side_effect=httpx.ConnectError("Connection refused"),
        )
        with pytest.raises(ProviderAPIError, match="request failed"):
            await provider.generate("system", "prompt")

    async def test_no_api_key(self, provider_no_key: GeminiProvider):
        with pytest.raises(ProviderAuthError, match="GEMINI_API_KEY"):
            await provider_no_key.generate("system", "prompt")


class TestGenerateStream:
    @respx.mock
    async def test_stream_success(self, provider: GeminiProvider):
        stream_data = (
            'data: {"candidates": [{"content": {"parts": '
            '[{"text": "Hello"}], "role": "model"}}]}\n\n'
            'data: {"candidates": [{"content": {"parts": '
            '[{"text": " World"}], "role": "model"}}]}\n\n'
        )
        respx.post(url__regex=r".*streamGenerateContent.*").mock(
            return_value=httpx.Response(200, text=stream_data),
        )
        chunks = []
        async for chunk in provider.generate_stream("system", "prompt"):
            chunks.append(chunk)
        assert "Hello" in chunks
        assert " World" in chunks

    @respx.mock
    async def test_stream_api_error(self, provider: GeminiProvider):
        respx.post(url__regex=r".*streamGenerateContent.*").mock(
            return_value=httpx.Response(429, text="Rate limited"),
        )
        with pytest.raises(ProviderAPIError, match="stream error"):
            async for _ in provider.generate_stream("system", "prompt"):
                pass

    @respx.mock
    async def test_stream_request_error(self, provider: GeminiProvider):
        respx.post(url__regex=r".*streamGenerateContent.*").mock(
            side_effect=httpx.ConnectError("fail"),
        )
        with pytest.raises(ProviderAPIError, match="stream request failed"):
            async for _ in provider.generate_stream("system", "prompt"):
                pass


class TestHealthcheck:
    @respx.mock
    async def test_healthy(self, provider: GeminiProvider):
        respx.post(GENERATE_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "candidates": [
                        {
                            "content": {
                                "parts": [{"text": "ok"}],
                                "role": "model",
                            }
                        }
                    ]
                },
            )
        )
        assert await provider.healthcheck() is True

    @respx.mock
    async def test_unhealthy(self, provider: GeminiProvider):
        respx.post(GENERATE_URL).mock(
            return_value=httpx.Response(500, text="error"),
        )
        assert await provider.healthcheck() is False

    async def test_no_key(self, provider_no_key: GeminiProvider):
        assert await provider_no_key.healthcheck() is False
