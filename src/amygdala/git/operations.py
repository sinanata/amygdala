"""Git subprocess wrapper."""

from __future__ import annotations

import subprocess
from pathlib import Path

from amygdala.exceptions import GitError, NotAGitRepoError


def _run(args: list[str], cwd: Path) -> str:
    """Run a git command and return stdout."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        raise GitError("git is not installed or not on PATH") from None
    except subprocess.CalledProcessError as exc:
        raise GitError(f"git {' '.join(args)} failed: {exc.stderr.strip()}") from exc
    return result.stdout


def is_git_repo(path: Path) -> bool:
    """Check whether path is inside a git repository."""
    try:
        _run(["rev-parse", "--is-inside-work-tree"], cwd=path)
    except GitError:
        return False
    return True


def ensure_git_repo(path: Path) -> None:
    """Raise NotAGitRepoError if path is not in a git repo."""
    if not is_git_repo(path):
        raise NotAGitRepoError(f"Not a git repository: {path}")


def get_repo_root(path: Path) -> Path:
    """Return the root of the git repository containing path."""
    ensure_git_repo(path)
    root = _run(["rev-parse", "--show-toplevel"], cwd=path).strip()
    return Path(root)


def get_current_branch(path: Path) -> str:
    """Return the current branch name."""
    ensure_git_repo(path)
    return _run(["rev-parse", "--abbrev-ref", "HEAD"], cwd=path).strip()


def get_tracked_files(path: Path) -> list[str]:
    """Return list of tracked file paths relative to repo root."""
    ensure_git_repo(path)
    output = _run(["ls-files"], cwd=path).strip()
    if not output:
        return []
    return output.splitlines()


def get_diff_names(path: Path, *, staged: bool = False) -> list[str]:
    """Return list of changed file paths."""
    ensure_git_repo(path)
    args = ["diff", "--name-only"]
    if staged:
        args.append("--cached")
    output = _run(args, cwd=path).strip()
    if not output:
        return []
    return output.splitlines()


def get_diff(path: Path, *, staged: bool = False, file_path: str | None = None) -> str:
    """Return raw diff output."""
    ensure_git_repo(path)
    args = ["diff"]
    if staged:
        args.append("--cached")
    if file_path:
        args.extend(["--", file_path])
    return _run(args, cwd=path)


def get_file_status(path: Path) -> dict[str, str]:
    """Return a mapping of file path -> short status code via git status --porcelain."""
    ensure_git_repo(path)
    output = _run(["status", "--porcelain"], cwd=path).rstrip()
    if not output:
        return {}
    result: dict[str, str] = {}
    for line in output.splitlines():
        # Format: XY filename (or XY orig -> renamed)
        # Porcelain XY is always positions 0-1; don't lstrip the line
        status_code = line[:2].strip()
        file_name = line[3:]
        # Handle renames
        if " -> " in file_name:
            file_name = file_name.split(" -> ", 1)[1]
        result[file_name] = status_code
    return result


def init_repo(path: Path) -> None:
    """Initialize a new git repo at path."""
    _run(["init"], cwd=path)


def add_files(path: Path, files: list[str]) -> None:
    """Stage files."""
    _run(["add", *files], cwd=path)


def commit(path: Path, message: str) -> str:
    """Create a commit and return the short hash."""
    _run(["commit", "-m", message], cwd=path)
    return _run(["rev-parse", "--short", "HEAD"], cwd=path).strip()
