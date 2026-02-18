"""Project-wide constants."""

from pathlib import Path

AMYGDALA_DIR = ".amygdala"
CONFIG_FILE = "config.toml"
INDEX_FILE = "index.json"
MEMORY_DIR = "memory"
SCHEMA_VERSION = 1

DEFAULT_GRANULARITY = "medium"
DEFAULT_PROVIDER = "anthropic"
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.0

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".kt", ".go",
    ".rs", ".c", ".cpp", ".h", ".hpp", ".cs", ".rb", ".php",
    ".swift", ".m", ".scala", ".sh", ".bash", ".zsh",
    ".yaml", ".yml", ".toml", ".json", ".xml", ".html", ".css",
    ".sql", ".md", ".txt", ".cfg", ".ini", ".env",
    ".dockerfile", ".tf", ".hcl",
})

MAX_FILE_SIZE_BYTES = 1_000_000  # 1 MB


def amygdala_dir(project_root: Path) -> Path:
    """Return the .amygdala directory for a project."""
    return project_root / AMYGDALA_DIR


def config_path(project_root: Path) -> Path:
    """Return the config file path."""
    return amygdala_dir(project_root) / CONFIG_FILE


def index_path(project_root: Path) -> Path:
    """Return the index file path."""
    return amygdala_dir(project_root) / INDEX_FILE


def memory_dir(project_root: Path) -> Path:
    """Return the memory directory path."""
    return amygdala_dir(project_root) / MEMORY_DIR
