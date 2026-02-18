"""SHA256 file hashing."""

from __future__ import annotations

import hashlib
from pathlib import Path

CHUNK_SIZE = 65536


def hash_file(file_path: Path) -> str:
    """Return the SHA256 hex digest of a file."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            sha.update(chunk)
    return sha.hexdigest()


def hash_content(content: str) -> str:
    """Return the SHA256 hex digest of a string."""
    return hashlib.sha256(content.encode()).hexdigest()
