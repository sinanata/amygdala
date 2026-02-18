"""Tests for OpenAI provider using respx mocks."""

from __future__ import annotations

import httpx
import pytest
import respx

from amygdala.exceptions import ProviderAPIError, ProviderAuthError
from amygdala.providers.openai import OpenAIProvider, OPENAI_API_URL


@pytest.fixture()
def provider() -> OpenAIProvider:
    return OpenAIProvider(model_name="gpt-4o-mini", api_key="test-key")


@pytest.fixture()
def provider_no_key() -> OpenAIProvider:
    return OpenAIProvider(model_name="gpt-4o-mini", api_key="")


class TestOpenAIProperties:
    def test_name(self, provider: OpenAIProvider):
        assert provider.name == "openai"

    def test_model(self, provider: OpenAIProvider):
        assert provider.model == "gpt-4o-mini"


class TestGenerate:
    @respx.mock
    async def test_success(self, provider: OpenAIProvider):
        respx.post(OPENAI_API_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "Hello from GPT"}, "finish_reason": "stop"}],
                    "model": "gpt-4o-mini",
                },
            )
        )
        result = await provider.generate("system", "user prompt")
        assert result == "Hello from GPT"

    @respx.mock
    async def test_api_error(self, provider: OpenAIProvider):
        respx.post(OPENAI_API_URL).mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        with pytest.raises(ProviderAPIError, match="500"):
            await provider.generate("system", "prompt")

    @respx.mock
    async def test_request_error(self, provider: OpenAIProvider):
        respx.post(OPENAI_API_URL).mock(side_effect=httpx.ConnectError("Connection refused"))
        with pytest.raises(ProviderAPIError, match="request failed"):
            await provider.generate("system", "prompt")

    async def test_no_api_key(self, provider_no_key: OpenAIProvider):
        with pytest.raises(ProviderAuthError, match="OPENAI_API_KEY"):
            await provider_no_key.generate("system", "prompt")


class TestGenerateStream:
    @respx.mock
    async def test_stream_success(self, provider: OpenAIProvider):
        stream_data = (
            'data: {"choices":[{"delta":{"content":"Hello"}}]}\n\n'
            'data: {"choices":[{"delta":{"content":" World"}}]}\n\n'
            'data: [DONE]\n\n'
        )
        respx.post(OPENAI_API_URL).mock(
            return_value=httpx.Response(200, text=stream_data)
        )
        chunks = []
        async for chunk in provider.generate_stream("system", "prompt"):
            chunks.append(chunk)
        assert "Hello" in chunks
        assert " World" in chunks

    @respx.mock
    async def test_stream_api_error(self, provider: OpenAIProvider):
        respx.post(OPENAI_API_URL).mock(
            return_value=httpx.Response(429, text="Rate limited")
        )
        with pytest.raises(ProviderAPIError, match="stream error"):
            async for _ in provider.generate_stream("system", "prompt"):
                pass

    @respx.mock
    async def test_stream_request_error(self, provider: OpenAIProvider):
        respx.post(OPENAI_API_URL).mock(side_effect=httpx.ConnectError("fail"))
        with pytest.raises(ProviderAPIError, match="stream request failed"):
            async for _ in provider.generate_stream("system", "prompt"):
                pass


class TestHealthcheck:
    @respx.mock
    async def test_healthy(self, provider: OpenAIProvider):
        respx.post(OPENAI_API_URL).mock(
            return_value=httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})
        )
        assert await provider.healthcheck() is True

    @respx.mock
    async def test_unhealthy(self, provider: OpenAIProvider):
        respx.post(OPENAI_API_URL).mock(
            return_value=httpx.Response(500, text="error")
        )
        assert await provider.healthcheck() is False

    async def test_no_key(self, provider_no_key: OpenAIProvider):
        assert await provider_no_key.healthcheck() is False
