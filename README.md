# Amygdala

AI coding assistants start every session with amnesia. **Amygdala** is a git-integrated memory system that tracks file summaries at configurable granularity levels, detects dirty files via `git diff`, and injects relevant context at session start.

- **Provider-agnostic** -- Anthropic, OpenAI, and Ollama supported out of the box
- **Adapter system** -- pluggable integration with Claude Code, Cursor, Windsurf (Claude Code ships first)
- **Git-native** -- summaries tracked alongside your code, dirty detection via content hashing

## Installation

### From PyPI

```bash
pip install amygdala
```

Install with a specific LLM provider:

```bash
pip install "amygdala[anthropic]"   # Anthropic (Claude)
pip install "amygdala[openai]"      # OpenAI (GPT)
pip install "amygdala[ollama]"      # Ollama (local models)
pip install "amygdala[all-providers]"  # All providers
```

### From source (development)

```bash
git clone https://github.com/sinanata/amygdala.git
cd amygdala
pip install -e ".[dev,all-providers]"
```

## Quick Start

### 1. Initialize in your project

```bash
cd /path/to/your/project
amygdala init --provider anthropic --model claude-haiku-4-5-20251001
```

This creates a `.amygdala/` directory with config and index files. Add `.amygdala/` to your `.gitignore` if you don't want to track memory across machines.

Options:
- `--provider` -- LLM provider: `anthropic`, `openai`, `ollama` (default: `anthropic`)
- `--model` -- Model identifier (default: `claude-haiku-4-5-20251001`)
- `--granularity` -- Summary detail level: `simple`, `medium`, `high` (default: `medium`)

### 2. Capture file summaries

```bash
# Capture specific files
amygdala capture src/main.py src/utils.py

# Capture all tracked files
amygdala capture --all

# Capture with high granularity
amygdala capture --all --granularity high
```

### 3. Check status

```bash
amygdala status          # Rich table output
amygdala status --json   # JSON output (for scripting / hooks)
```

### 4. Detect dirty files

```bash
amygdala diff                          # Scan for files changed since last capture
amygdala diff --mark-dirty src/main.py # Manually mark a file as dirty
```

### 5. Install a platform adapter

```bash
amygdala install claude-code    # Install Claude Code hooks + MCP server
amygdala uninstall claude-code  # Remove adapter
```

## Environment Variables

Set your API key for the provider you're using:

| Provider   | Variable             |
|------------|----------------------|
| Anthropic  | `ANTHROPIC_API_KEY`  |
| OpenAI     | `OPENAI_API_KEY`     |
| Ollama     | *(none -- local)*    |

## CLI Reference

| Command               | Description                                  |
|-----------------------|----------------------------------------------|
| `amygdala init`       | Initialize Amygdala in a project             |
| `amygdala capture`    | Capture file summaries (specific or `--all`) |
| `amygdala status`     | Show project memory status                   |
| `amygdala diff`       | Scan for dirty files                         |
| `amygdala config show`| Show current configuration                   |
| `amygdala config get` | Get a config value (dot notation)            |
| `amygdala install`    | Install a platform adapter                   |
| `amygdala uninstall`  | Remove a platform adapter                    |
| `amygdala serve`      | Start the MCP server                         |
| `amygdala clean`      | Remove all `.amygdala/` data (`--force`)     |

## Claude Code Integration

After installing the Claude Code adapter, Amygdala provides:

**Hooks:**
- **SessionStart** -- injects branch info, tracked/dirty file counts into session context
- **PostToolUse** -- marks files dirty when Claude Code writes or edits them

**MCP Server** (5 tools available to Claude):
- `get_file_summary(file_path)` -- retrieve a file's cached summary
- `get_project_overview()` -- project-wide memory status
- `list_dirty_files()` -- files changed since last capture
- `capture_file(file_path, granularity)` -- capture or update a file's summary
- `search_memory(query)` -- search across all stored summaries

Start the MCP server:

```bash
amygdala serve
```

## Project Structure

```
.amygdala/
  config.toml     # Provider, model, granularity settings
  index.json      # Per-file tracking (hash, status, timestamps)
  memory/         # Markdown summaries mirroring your source tree
    src/
      main.py.md
      utils.py.md
```

## Granularity Levels

| Level    | Description                                                     |
|----------|-----------------------------------------------------------------|
| `simple` | One-line purpose of the file                                    |
| `medium` | Purpose, key functions/classes, dependencies (default)          |
| `high`   | Detailed breakdown: every function, class, import, side-effect  |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev,all-providers]"

# Run tests
pytest

# Run with coverage
pytest --cov=amygdala --cov-report=term

# Lint
ruff check src/ tests/
ruff format src/ tests/

# Type check
mypy src/amygdala/
```

## Requirements

- Python >= 3.12
- Git (project must be a git repository)

## License

MIT
