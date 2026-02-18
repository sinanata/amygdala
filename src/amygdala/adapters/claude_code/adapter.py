"""Claude Code platform adapter."""

from __future__ import annotations

import json
from pathlib import Path

from amygdala.adapters.base import PlatformAdapter
from amygdala.adapters.claude_code.hooks import (
    generate_hooks_config,
    render_post_tool_use_hook,
    render_session_start_hook,
)
from amygdala.core.dirty_tracker import get_dirty_files, mark_file_dirty
from amygdala.core.engine import AmygdalaEngine


class ClaudeCodeAdapter(PlatformAdapter):
    """Adapter for Claude Code (hooks + MCP server)."""

    @property
    def name(self) -> str:
        return "claude-code"

    def install(self, project_root: Path) -> None:
        """Install Claude Code hooks and register MCP server."""
        hooks_dir = project_root / ".amygdala" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        # Write hook scripts
        session_script = hooks_dir / "session_start.sh"
        session_script.write_text(render_session_start_hook(project_root), encoding="utf-8")

        post_tool_script = hooks_dir / "post_tool_use.sh"
        post_tool_script.write_text(render_post_tool_use_hook(project_root), encoding="utf-8")

        # Write hooks config
        config = generate_hooks_config(project_root)
        config_path = hooks_dir / "claude_hooks.json"
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    def uninstall(self, project_root: Path) -> None:
        """Remove Claude Code hooks."""
        import shutil
        hooks_dir = project_root / ".amygdala" / "hooks"
        if hooks_dir.exists():
            shutil.rmtree(hooks_dir)

    def status(self, project_root: Path) -> dict:
        """Get adapter status."""
        hooks_dir = project_root / ".amygdala" / "hooks"
        return {
            "adapter": self.name,
            "installed": hooks_dir.exists(),
            "hooks_dir": str(hooks_dir),
            "session_start_hook": (hooks_dir / "session_start.sh").exists() if hooks_dir.exists() else False,
            "post_tool_use_hook": (hooks_dir / "post_tool_use.sh").exists() if hooks_dir.exists() else False,
        }

    def get_context_for_session(self, project_root: Path) -> str:
        """Build context string for a new Claude Code session."""
        try:
            engine = AmygdalaEngine(project_root)
            data = engine.status()
            lines = [
                f"Branch: {data['branch']}",
                f"Tracked: {data['total_tracked']} files",
                f"Captured: {data['total_captured']} summaries",
                f"Dirty: {data['dirty_files']} files",
            ]
            if data["dirty_list"]:
                lines.append("Dirty files: " + ", ".join(data["dirty_list"]))
            return "\n".join(lines)
        except Exception:
            return ""

    def on_file_changed(self, project_root: Path, file_path: str) -> None:
        """Mark a file as dirty when Claude Code edits it."""
        mark_file_dirty(project_root, file_path)
