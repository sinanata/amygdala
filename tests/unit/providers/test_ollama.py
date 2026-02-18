"""Tests for Ollama provider using respx mocks."""

from __future__ import annotations

import httpx
import pytest
import respx

from amygdala.exceptions import ProviderAPIError
from amygdala.providers.ollama import OllamaProvider, OLLAMA_API_URL


@pytest.fixture()
def provider() -> OllamaProvider:
    return OllamaProvider(model_name="llama3")


class TestOllamaProperties:
    def test_name(self, provider: OllamaProvider):
        assert provider.name == "ollama"

    def test_model(self, provider: OllamaProvider):
        assert provider.model == "llama3"


class TestGenerate:
    @respx.mock
    async def test_success(self, provider: OllamaProvider):
        respx.post(OLLAMA_API_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "message": {"role": "assistant", "content": "Hello from Llama"},
                    "done": True,
                },
            )
        )
        result = await provider.generate("system", "user prompt")
        assert result == "Hello from Llama"

    @respx.mock
    async def test_api_error(self, provider: OllamaProvider):
        respx.post(OLLAMA_API_URL).mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        with pytest.raises(ProviderAPIError, match="500"):
            await provider.generate("system", "prompt")

    @respx.mock
    async def test_request_error(self, provider: OllamaProvider):
        respx.post(OLLAMA_API_URL).mock(side_effect=httpx.ConnectError("Connection refused"))
        with pytest.raises(ProviderAPIError, match="request failed"):
            await provider.generate("system", "prompt")


class TestGenerateStream:
    @respx.mock
    async def test_stream_success(self, provider: OllamaProvider):
        stream_data = (
            '{"message":{"content":"Hello"},"done":false}\n'
            '{"message":{"content":" World"},"done":false}\n'
            '{"message":{"content":""},"done":true}\n'
        )
        respx.post(OLLAMA_API_URL).mock(
            return_value=httpx.Response(200, text=stream_data)
        )
        chunks = []
        async for chunk in provider.generate_stream("system", "prompt"):
            chunks.append(chunk)
        assert "Hello" in chunks
        assert " World" in chunks

    @respx.mock
    async def test_stream_api_error(self, provider: OllamaProvider):
        respx.post(OLLAMA_API_URL).mock(
            return_value=httpx.Response(500, text="error")
        )
        with pytest.raises(ProviderAPIError, match="stream error"):
            async for _ in provider.generate_stream("system", "prompt"):
                pass

    @respx.mock
    async def test_stream_request_error(self, provider: OllamaProvider):
        respx.post(OLLAMA_API_URL).mock(side_effect=httpx.ConnectError("fail"))
        with pytest.raises(ProviderAPIError, match="stream request failed"):
            async for _ in provider.generate_stream("system", "prompt"):
                pass


class TestHealthcheck:
    @respx.mock
    async def test_healthy(self, provider: OllamaProvider):
        respx.get("http://localhost:11434/api/tags").mock(
            return_value=httpx.Response(200, json={"models": []})
        )
        assert await provider.healthcheck() is True

    @respx.mock
    async def test_unhealthy(self, provider: OllamaProvider):
        respx.get("http://localhost:11434/api/tags").mock(
            side_effect=httpx.ConnectError("fail")
        )
        assert await provider.healthcheck() is False
