"""Hook script generation for Claude Code."""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, DictLoader

SESSION_START_TEMPLATE = """\
#!/usr/bin/env bash
# Amygdala session start hook for Claude Code
# Auto-generated — do not edit manually

STATUS_JSON=$(amygdala status --json --dir "{{ project_root }}" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$STATUS_JSON"
fi
"""

POST_TOOL_USE_TEMPLATE = """\
#!/usr/bin/env bash
# Amygdala post-tool-use hook for Claude Code
# Auto-generated — do not edit manually

# Read tool input from stdin
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null)
FILE_PATH=$(echo "$INPUT" | python -c "import sys,json; d=json.load(sys.stdin); inp=d.get('tool_input',{}); print(inp.get('file_path', inp.get('path','')))" 2>/dev/null)

if [ "$TOOL_NAME" = "Write" ] || [ "$TOOL_NAME" = "Edit" ]; then
    if [ -n "$FILE_PATH" ]; then
        amygdala diff --mark-dirty "$FILE_PATH" --dir "{{ project_root }}" 2>/dev/null
    fi
fi
"""


_env = Environment(loader=DictLoader({
    "session_start.sh": SESSION_START_TEMPLATE,
    "post_tool_use.sh": POST_TOOL_USE_TEMPLATE,
}))


def render_session_start_hook(project_root: Path) -> str:
    """Render the session start hook script."""
    template = _env.get_template("session_start.sh")
    return template.render(project_root=str(project_root).replace("\\", "/"))


def render_post_tool_use_hook(project_root: Path) -> str:
    """Render the post-tool-use hook script."""
    template = _env.get_template("post_tool_use.sh")
    return template.render(project_root=str(project_root).replace("\\", "/"))


def generate_hooks_config(project_root: Path) -> dict:
    """Generate the Claude Code hooks configuration."""
    return {
        "hooks": [
            {
                "matcher": "SessionStart",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"amygdala status --json --dir \"{project_root}\"",
                    }
                ],
            },
            {
                "matcher": "Write|Edit",
                "hooks": [
                    {
                        "type": "command",
                        "command": "amygdala diff --mark-dirty \"$FILE_PATH\"",
                    }
                ],
            },
        ]
    }
