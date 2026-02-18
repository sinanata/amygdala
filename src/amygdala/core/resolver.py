"""Source path to memory path mapping."""

from __future__ import annotations

from pathlib import PurePosixPath


def source_to_memory_path(relative_path: str) -> str:
    """Convert a source file relative path to its memory file relative path.

    e.g. 'src/main.py' -> 'src/main.py.md'
    """
    return relative_path + ".md"


def memory_to_source_path(memory_relative: str) -> str:
    """Convert a memory file relative path back to source relative path.

    e.g. 'src/main.py.md' -> 'src/main.py'
    """
    if memory_relative.endswith(".md"):
        return memory_relative[:-3]
    return memory_relative


def detect_language(file_path: str) -> str | None:
    """Detect the programming language from file extension."""
    ext_map: dict[str, str] = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".kt": "kotlin",
        ".go": "go",
        ".rs": "rust",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".scala": "scala",
        ".sh": "shell",
        ".bash": "shell",
        ".zsh": "shell",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".json": "json",
        ".xml": "xml",
        ".html": "html",
        ".css": "css",
        ".sql": "sql",
        ".md": "markdown",
    }
    suffix = PurePosixPath(file_path).suffix.lower()
    return ext_map.get(suffix)
