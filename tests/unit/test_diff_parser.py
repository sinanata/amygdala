"""Tests for git diff parser."""

from __future__ import annotations

from amygdala.git.diff_parser import (
    DiffHunk,
    FileDiff,
    _parse_hunk_header,
    _parse_range,
    parse_diff,
)


class TestParseRange:
    def test_with_comma(self):
        assert _parse_range("1,3") == (1, 3)

    def test_without_comma(self):
        assert _parse_range("5") == (5, 1)


class TestParseHunkHeader:
    def test_standard_header(self):
        hunk = _parse_hunk_header("@@ -1,3 +1,5 @@ some context")
        assert hunk is not None
        assert hunk.old_start == 1
        assert hunk.old_count == 3
        assert hunk.new_start == 1
        assert hunk.new_count == 5

    def test_single_line_range(self):
        hunk = _parse_hunk_header("@@ -1 +1,2 @@")
        assert hunk is not None
        assert hunk.old_count == 1

    def test_invalid_header(self):
        assert _parse_hunk_header("not a hunk") is None


class TestParseDiff:
    def test_empty_diff(self):
        assert parse_diff("") == []
        assert parse_diff("  \n  ") == []

    def test_single_file_modify(self):
        raw = """diff --git a/README.md b/README.md
index abc1234..def5678 100644
--- a/README.md
+++ b/README.md
@@ -1,3 +1,4 @@
 # Title
+New line
 Existing line
 Another line"""
        diffs = parse_diff(raw)
        assert len(diffs) == 1
        d = diffs[0]
        assert d.path == "README.md"
        assert not d.is_new
        assert not d.is_deleted
        assert not d.is_renamed
        assert len(d.hunks) == 1
        assert d.added_lines == 1
        assert d.removed_lines == 0

    def test_new_file(self):
        raw = """diff --git a/new.py b/new.py
new file mode 100644
index 0000000..abc1234
--- /dev/null
+++ b/new.py
@@ -0,0 +1,2 @@
+print("hello")
+print("world")"""
        diffs = parse_diff(raw)
        assert len(diffs) == 1
        assert diffs[0].is_new is True
        assert diffs[0].added_lines == 2

    def test_deleted_file(self):
        raw = """diff --git a/old.py b/old.py
deleted file mode 100644
index abc1234..0000000
--- a/old.py
+++ /dev/null
@@ -1,2 +0,0 @@
-print("hello")
-print("world")"""
        diffs = parse_diff(raw)
        assert len(diffs) == 1
        assert diffs[0].is_deleted is True
        assert diffs[0].removed_lines == 2

    def test_renamed_file(self):
        raw = """diff --git a/old_name.py b/new_name.py
similarity index 100%
rename from old_name.py
rename to new_name.py"""
        diffs = parse_diff(raw)
        assert len(diffs) == 1
        assert diffs[0].is_renamed is True
        assert diffs[0].old_path == "old_name.py"
        assert diffs[0].path == "new_name.py"

    def test_multiple_files(self):
        raw = """diff --git a/a.py b/a.py
index abc..def 100644
--- a/a.py
+++ b/a.py
@@ -1,1 +1,2 @@
 existing
+added
diff --git a/b.py b/b.py
index abc..def 100644
--- a/b.py
+++ b/b.py
@@ -1,2 +1,1 @@
 keep
-removed"""
        diffs = parse_diff(raw)
        assert len(diffs) == 2
        assert diffs[0].path == "a.py"
        assert diffs[1].path == "b.py"

    def test_multiple_hunks(self):
        raw = """diff --git a/big.py b/big.py
index abc..def 100644
--- a/big.py
+++ b/big.py
@@ -1,3 +1,4 @@
 line1
+inserted
 line2
 line3
@@ -10,3 +11,4 @@
 line10
+another
 line11
 line12"""
        diffs = parse_diff(raw)
        assert len(diffs) == 1
        assert len(diffs[0].hunks) == 2


class TestFileDiffProperties:
    def test_added_lines(self):
        fd = FileDiff(
            path="test.py",
            hunks=[DiffHunk(1, 1, 1, 2, ["+line", " ctx"])],
        )
        assert fd.added_lines == 1

    def test_removed_lines(self):
        fd = FileDiff(
            path="test.py",
            hunks=[DiffHunk(1, 2, 1, 1, ["-line", " ctx"])],
        )
        assert fd.removed_lines == 1

    def test_empty_hunks(self):
        fd = FileDiff(path="test.py")
        assert fd.added_lines == 0
        assert fd.removed_lines == 0
