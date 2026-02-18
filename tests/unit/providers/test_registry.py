"""Tests for provider registry."""

from __future__ import annotations

import pytest

from amygdala.exceptions import ProviderNotFoundError
from amygdala.providers.base import LLMProvider
from amygdala.providers.registry import get_provider_class, list_providers


class TestListProviders:
    def test_lists_registered_providers(self):
        providers = list_providers()
        assert "anthropic" in providers
        assert "openai" in providers
        assert "ollama" in providers

    def test_returns_sorted(self):
        providers = list_providers()
        assert providers == sorted(providers)


class TestGetProviderClass:
    def test_get_anthropic(self):
        cls = get_provider_class("anthropic")
        assert issubclass(cls, LLMProvider)

    def test_get_nonexistent(self):
        with pytest.raises(ProviderNotFoundError, match="nonexistent"):
            get_provider_class("nonexistent")
