"""Tests for Claude Code hook generation."""

from __future__ import annotations

from pathlib import Path

from amygdala.adapters.claude_code.hooks import (
    generate_hooks_config,
    render_post_tool_use_hook,
    render_session_start_hook,
)


class TestRenderSessionStartHook:
    def test_contains_amygdala_command(self, tmp_path: Path):
        result = render_session_start_hook(tmp_path)
        assert "amygdala status --json" in result
        assert "#!/usr/bin/env bash" in result

    def test_contains_project_root(self, tmp_path: Path):
        result = render_session_start_hook(tmp_path)
        # Path is normalized to forward slashes
        assert str(tmp_path).replace("\\", "/") in result


class TestRenderPostToolUseHook:
    def test_contains_diff_command(self, tmp_path: Path):
        result = render_post_tool_use_hook(tmp_path)
        assert "amygdala diff --mark-dirty" in result

    def test_contains_write_edit_check(self, tmp_path: Path):
        result = render_post_tool_use_hook(tmp_path)
        assert "Write" in result
        assert "Edit" in result


class TestGenerateHooksConfig:
    def test_has_hooks_key(self, tmp_path: Path):
        config = generate_hooks_config(tmp_path)
        assert "hooks" in config
        assert len(config["hooks"]) == 2

    def test_session_start_matcher(self, tmp_path: Path):
        config = generate_hooks_config(tmp_path)
        assert config["hooks"][0]["matcher"] == "SessionStart"

    def test_write_edit_matcher(self, tmp_path: Path):
        config = generate_hooks_config(tmp_path)
        assert config["hooks"][1]["matcher"] == "Write|Edit"
