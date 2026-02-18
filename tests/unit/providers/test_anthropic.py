"""Tests for Anthropic provider using respx mocks."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from amygdala.exceptions import ProviderAPIError, ProviderAuthError
from amygdala.providers.anthropic import AnthropicProvider, ANTHROPIC_API_URL


@pytest.fixture()
def provider() -> AnthropicProvider:
    return AnthropicProvider(
        model_name="claude-haiku-4-5-20251001",
        api_key="test-key",
    )


@pytest.fixture()
def provider_no_key() -> AnthropicProvider:
    return AnthropicProvider(model_name="claude-haiku-4-5-20251001", api_key="")


class TestAnthropicProperties:
    def test_name(self, provider: AnthropicProvider):
        assert provider.name == "anthropic"

    def test_model(self, provider: AnthropicProvider):
        assert provider.model == "claude-haiku-4-5-20251001"


class TestGenerate:
    @respx.mock
    async def test_success(self, provider: AnthropicProvider):
        respx.post(ANTHROPIC_API_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "content": [{"type": "text", "text": "Hello from Claude"}],
                    "model": "claude-haiku-4-5-20251001",
                    "stop_reason": "end_turn",
                },
            )
        )
        result = await provider.generate("system", "user prompt")
        assert result == "Hello from Claude"

    @respx.mock
    async def test_api_error(self, provider: AnthropicProvider):
        respx.post(ANTHROPIC_API_URL).mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        with pytest.raises(ProviderAPIError, match="500"):
            await provider.generate("system", "prompt")

    @respx.mock
    async def test_request_error(self, provider: AnthropicProvider):
        respx.post(ANTHROPIC_API_URL).mock(side_effect=httpx.ConnectError("Connection refused"))
        with pytest.raises(ProviderAPIError, match="request failed"):
            await provider.generate("system", "prompt")

    async def test_no_api_key(self, provider_no_key: AnthropicProvider):
        with pytest.raises(ProviderAuthError, match="ANTHROPIC_API_KEY"):
            await provider_no_key.generate("system", "prompt")


class TestGenerateStream:
    @respx.mock
    async def test_stream_success(self, provider: AnthropicProvider):
        stream_data = (
            'data: {"type": "content_block_delta", "delta": {"text": "Hello"}}\n\n'
            'data: {"type": "content_block_delta", "delta": {"text": " World"}}\n\n'
            'data: {"type": "message_stop"}\n\n'
        )
        respx.post(ANTHROPIC_API_URL).mock(
            return_value=httpx.Response(200, text=stream_data)
        )
        chunks = []
        async for chunk in provider.generate_stream("system", "prompt"):
            chunks.append(chunk)
        assert "Hello" in chunks
        assert " World" in chunks

    @respx.mock
    async def test_stream_api_error(self, provider: AnthropicProvider):
        respx.post(ANTHROPIC_API_URL).mock(
            return_value=httpx.Response(429, text="Rate limited")
        )
        with pytest.raises(ProviderAPIError, match="stream error"):
            async for _ in provider.generate_stream("system", "prompt"):
                pass

    @respx.mock
    async def test_stream_request_error(self, provider: AnthropicProvider):
        respx.post(ANTHROPIC_API_URL).mock(side_effect=httpx.ConnectError("fail"))
        with pytest.raises(ProviderAPIError, match="stream request failed"):
            async for _ in provider.generate_stream("system", "prompt"):
                pass


class TestHealthcheck:
    @respx.mock
    async def test_healthy(self, provider: AnthropicProvider):
        respx.post(ANTHROPIC_API_URL).mock(
            return_value=httpx.Response(200, json={"content": [{"text": "ok"}]})
        )
        assert await provider.healthcheck() is True

    @respx.mock
    async def test_unhealthy(self, provider: AnthropicProvider):
        respx.post(ANTHROPIC_API_URL).mock(
            return_value=httpx.Response(500, text="error")
        )
        assert await provider.healthcheck() is False

    async def test_no_key(self, provider_no_key: AnthropicProvider):
        assert await provider_no_key.healthcheck() is False
