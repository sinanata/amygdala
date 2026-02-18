"""Directory layout conventions for .amygdala/."""

from __future__ import annotations

from pathlib import Path

from amygdala.constants import AMYGDALA_DIR, CONFIG_FILE, INDEX_FILE, MEMORY_DIR


def get_amygdala_dir(project_root: Path) -> Path:
    return project_root / AMYGDALA_DIR


def get_config_path(project_root: Path) -> Path:
    return get_amygdala_dir(project_root) / CONFIG_FILE


def get_index_path(project_root: Path) -> Path:
    return get_amygdala_dir(project_root) / INDEX_FILE


def get_memory_dir(project_root: Path) -> Path:
    return get_amygdala_dir(project_root) / MEMORY_DIR


def ensure_layout(project_root: Path) -> None:
    """Create .amygdala directory structure if it doesn't exist."""
    get_amygdala_dir(project_root).mkdir(exist_ok=True)
    get_memory_dir(project_root).mkdir(exist_ok=True)


def memory_path_for_file(project_root: Path, relative_path: str) -> Path:
    """Compute the memory .md file path for a source file."""
    return get_memory_dir(project_root) / (relative_path + ".md")
