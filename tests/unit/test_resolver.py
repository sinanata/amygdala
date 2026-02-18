"""Tests for path resolver and language detection."""

from __future__ import annotations

import pytest

from amygdala.core.resolver import (
    detect_language,
    memory_to_source_path,
    source_to_memory_path,
)


class TestSourceToMemoryPath:
    def test_simple(self):
        assert source_to_memory_path("src/main.py") == "src/main.py.md"

    def test_nested(self):
        assert source_to_memory_path("a/b/c.ts") == "a/b/c.ts.md"

    def test_root_file(self):
        assert source_to_memory_path("README.md") == "README.md.md"


class TestMemoryToSourcePath:
    def test_simple(self):
        assert memory_to_source_path("src/main.py.md") == "src/main.py"

    def test_no_md_suffix(self):
        assert memory_to_source_path("src/main.py") == "src/main.py"


class TestDetectLanguage:
    @pytest.mark.parametrize(
        "path,expected",
        [
            ("main.py", "python"),
            ("app.js", "javascript"),
            ("lib.ts", "typescript"),
            ("Component.jsx", "javascript"),
            ("Component.tsx", "typescript"),
            ("Main.java", "java"),
            ("main.go", "go"),
            ("lib.rs", "rust"),
            ("main.c", "c"),
            ("main.cpp", "cpp"),
            ("lib.h", "c"),
            ("lib.hpp", "cpp"),
            ("Class.cs", "csharp"),
            ("app.rb", "ruby"),
            ("index.php", "php"),
            ("App.swift", "swift"),
            ("Main.scala", "scala"),
            ("script.sh", "shell"),
            ("script.bash", "shell"),
            ("config.yaml", "yaml"),
            ("config.yml", "yaml"),
            ("config.toml", "toml"),
            ("data.json", "json"),
            ("page.html", "html"),
            ("style.css", "css"),
            ("query.sql", "sql"),
            ("README.md", "markdown"),
            ("layout.xml", "xml"),
            ("script.zsh", "shell"),
            ("main.kt", "kotlin"),
        ],
    )
    def test_known_extensions(self, path: str, expected: str):
        assert detect_language(path) == expected

    def test_unknown_extension(self):
        assert detect_language("file.xyz") is None

    def test_no_extension(self):
        assert detect_language("Makefile") is None
