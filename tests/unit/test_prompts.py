"""Tests for prompt templates."""

from __future__ import annotations

import pytest

from amygdala.models.enums import Granularity
from amygdala.prompts.templates import format_user_prompt, get_prompts
from amygdala.prompts.simple import SIMPLE_SYSTEM, SIMPLE_USER
from amygdala.prompts.medium import MEDIUM_SYSTEM, MEDIUM_USER
from amygdala.prompts.high import HIGH_SYSTEM, HIGH_USER


class TestGetPrompts:
    @pytest.mark.parametrize(
        "granularity,expected_system",
        [
            (Granularity.SIMPLE, SIMPLE_SYSTEM),
            (Granularity.MEDIUM, MEDIUM_SYSTEM),
            (Granularity.HIGH, HIGH_SYSTEM),
        ],
    )
    def test_returns_correct_system_prompt(self, granularity, expected_system):
        system, _ = get_prompts(granularity)
        assert system == expected_system

    @pytest.mark.parametrize(
        "granularity,expected_user",
        [
            (Granularity.SIMPLE, SIMPLE_USER),
            (Granularity.MEDIUM, MEDIUM_USER),
            (Granularity.HIGH, HIGH_USER),
        ],
    )
    def test_returns_correct_user_template(self, granularity, expected_user):
        _, user = get_prompts(granularity)
        assert user == expected_user


class TestFormatUserPrompt:
    def test_simple(self):
        result = format_user_prompt(
            Granularity.SIMPLE,
            file_path="src/main.py",
            language="python",
            content="print('hello')",
        )
        assert "src/main.py" in result
        assert "python" in result
        assert "print('hello')" in result

    def test_medium(self):
        result = format_user_prompt(
            Granularity.MEDIUM,
            file_path="app.js",
            language="javascript",
            content="const x = 1;",
        )
        assert "app.js" in result
        assert "javascript" in result

    def test_high(self):
        result = format_user_prompt(
            Granularity.HIGH,
            file_path="lib.rs",
            language="rust",
            content="fn main() {}",
        )
        assert "lib.rs" in result
        assert "rust" in result

    def test_unknown_language(self):
        result = format_user_prompt(
            Granularity.SIMPLE,
            file_path="Makefile",
            language=None,
            content="all: build",
        )
        assert "unknown" in result

    @pytest.mark.parametrize("granularity", list(Granularity))
    def test_all_templates_have_placeholders(self, granularity):
        """Verify all templates can be formatted without error."""
        result = format_user_prompt(
            granularity,
            file_path="test.py",
            language="python",
            content="x = 1",
        )
        assert "test.py" in result
