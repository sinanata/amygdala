# Amygdala

AI coding assistants start every session with amnesia. **Amygdala** is a git-integrated memory system that tracks file summaries at configurable granularity levels, detects dirty files via `git diff`, and injects relevant context at session start.

- **Provider-agnostic** -- Anthropic, OpenAI, Google Gemini, and Ollama supported out of the box
- **Adapter system** -- pluggable integration with Claude Code, Cursor, Windsurf (Claude Code ships first)
- **Git-native** -- summaries tracked alongside your code, dirty detection via content hashing
- **Extension profiles** -- opt-in to framework-specific file types (Unity, Unreal, Python, Node, React, Next.js)
- **Auto-capture** -- MCP-driven summary refresh using your Claude Code subscription (no API key needed)

## Installation

### From PyPI

```bash
pip install amygdala
```

Install with a specific LLM provider:

```bash
pip install "amygdala[anthropic]"   # Anthropic (Claude)
pip install "amygdala[openai]"      # OpenAI (GPT)
pip install "amygdala[gemini]"      # Google Gemini
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
- `--provider` -- LLM provider: `anthropic`, `openai`, `gemini`, `ollama` (default: `anthropic`)
- `--model` -- Model identifier (default: `claude-haiku-4-5-20251001`)
- `--granularity` -- Summary detail level: `simple`, `medium`, `high` (default: `medium`)
- `--profile` / `-p` -- Extension profile to enable (repeatable, see [Extension Profiles](#extension-profiles))
- `--auto-capture` / `--no-auto-capture` -- MCP-driven auto-capture (default: enabled)

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

## Auto-Capture (MCP-Driven)

When `auto_capture` is enabled (the default), Amygdala keeps file summaries fresh **using your Claude Code subscription** -- no separate API key needed.

### How it works

1. **PostToolUse hook** marks files dirty whenever Claude Code edits them
2. **SessionStart hook** injects project status (including dirty file list) into the session context
3. When Claude sees stale files in context, it uses the **`store_summary` MCP tool** to refresh them
4. Claude reads the file, writes a summary, and passes it to `store_summary()` -- the file is marked clean

The key insight: Claude Code *is* the LLM. Instead of making a separate API call to generate summaries, Claude generates them as part of its normal session activity.

### Two capture modes

| Mode | Who generates the summary | API key needed? | When to use |
|------|--------------------------|-----------------|-------------|
| **MCP-driven** (default) | Claude Code itself | No | During active Claude Code sessions |
| **CLI-driven** (opt-in) | Anthropic / OpenAI / Ollama API | Yes | Batch capture, CI, non-Claude workflows |

### Disabling auto-capture

```bash
amygdala init --no-auto-capture
```

When disabled, the session context omits the auto-capture hint. You can still use `amygdala capture` with an API key, or manually call the MCP tools.

## Extension Profiles

The base capture pipeline supports common source and config file types (`.py`, `.js`, `.ts`, `.json`, `.yaml`, etc.). Extension profiles add framework-specific file types, language mappings, and exclude patterns on top of this base set.

Enable profiles at init time with `--profile` / `-p` (repeatable):

```bash
# Single profile
amygdala init --profile unity

# Multiple profiles
amygdala init -p node -p react

# Check active profiles
amygdala config get profiles
amygdala status
```

### Available Profiles

| Profile | Key Extensions | Excludes |
|---------|---------------|----------|
| **unity** | `.shader`, `.hlsl`, `.cginc`, `.compute`, `.unity`, `.prefab`, `.asset`, `.mat`, `.meta`, `.asmdef`, `.asmref`, `.shadergraph`, `.uxml`, `.uss` | `Library/`, `Temp/`, `Obj/`, `UserSettings/`, `Logs/` |
| **unreal** | `.inl`, `.uproject`, `.uplugin`, `.usf`, `.ush`, `.uasset`, `.umap` | `Binaries/`, `DerivedDataCache/`, `Intermediate/`, `Saved/` |
| **python** | `.pyi`, `.pyx`, `.pxd`, `.ipynb`, `.in`, `.conf` | `__pycache__/`, `.venv/`, `.tox/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/` |
| **node** | `.mjs`, `.cjs`, `.mts`, `.cts`, `.npmrc` | `node_modules/`, `.next/`, `.nuxt/`, `.cache/`, `.turbo/` |
| **react** | `.scss`, `.sass`, `.less`, `.svg`, `.mdx` | `node_modules/`, `storybook-static/`, `coverage/` |
| **nextjs** | `.mdx`, `.scss`, `.svg` | `.next/`, `.vercel/`, `out/`, `node_modules/` |

Profiles compose via set-union -- enabling both `node` and `react` gives you all extensions from both. Language detection is also extended (e.g., `.shader` maps to `shaderlab`, `.pyi` maps to `python`).

## Environment Variables

Set your API key for the provider you're using (only needed for CLI-driven capture):

| Provider   | Variable                               |
|------------|----------------------------------------|
| Anthropic  | `ANTHROPIC_API_KEY`                    |
| OpenAI     | `OPENAI_API_KEY`                       |
| Gemini     | `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) |
| Ollama     | *(none -- local)*                      |

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
- **SessionStart** -- injects branch info, tracked/dirty file counts, and auto-capture hints into session context
- **PostToolUse** -- marks files dirty when Claude Code writes or edits them

**MCP Server** (7 tools available to Claude):
- `get_file_summary(file_path)` -- retrieve a file's cached summary
- `get_project_overview()` -- project-wide memory status
- `list_dirty_files()` -- files changed since last capture
- `capture_file(file_path, granularity)` -- capture using the configured LLM provider (requires API key)
- `read_file_for_capture(file_path)` -- read file content for summary generation
- `store_summary(file_path, summary, granularity)` -- store a summary you wrote (no API key needed)
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
