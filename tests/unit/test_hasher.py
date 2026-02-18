"""Tests for SHA256 file hashing."""

from __future__ import annotations

import hashlib
from pathlib import Path

from amygdala.core.hasher import hash_content, hash_file


class TestHashFile:
    def test_hash_file(self, tmp_path: Path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        result = hash_file(f)
        expected = hashlib.sha256(b"hello world").hexdigest()
        assert result == expected

    def test_hash_empty_file(self, tmp_path: Path):
        f = tmp_path / "empty.txt"
        f.write_bytes(b"")
        result = hash_file(f)
        expected = hashlib.sha256(b"").hexdigest()
        assert result == expected

    def test_hash_binary_file(self, tmp_path: Path):
        f = tmp_path / "binary.bin"
        data = bytes(range(256))
        f.write_bytes(data)
        result = hash_file(f)
        expected = hashlib.sha256(data).hexdigest()
        assert result == expected


class TestHashContent:
    def test_hash_string(self):
        result = hash_content("test")
        expected = hashlib.sha256(b"test").hexdigest()
        assert result == expected

    def test_hash_empty_string(self):
        result = hash_content("")
        expected = hashlib.sha256(b"").hexdigest()
        assert result == expected
