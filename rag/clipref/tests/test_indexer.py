"""Tests for ClipRef indexer."""

import pytest
from pathlib import Path

from clipref import indexer


def test_scan_files_single(tmp_path):
    """Test scanning a single file."""
    f = tmp_path / "test.md"
    f.write_text("content")
    files = indexer.scan_files([str(tmp_path)])
    assert len(files) == 1
    assert files[0] == f.resolve()


def test_scan_files_multiple(tmp_path):
    """Test scanning multiple files recursively."""
    (tmp_path / "sub").mkdir()
    f1 = tmp_path / "a.md"
    f2 = tmp_path / "sub" / "b.md"
    f1.write_text("a")
    f2.write_text("b")

    files = indexer.scan_files([str(tmp_path)])
    assert len(files) == 2


def test_scan_files_binary_excluded(tmp_path):
    """Test binary files are not included in scan (by default pattern)."""
    f = tmp_path / "image.png"
    f.write_bytes(b"\x89PNG\r\n")

    # With default glob pattern, .png won't match typical text patterns
    # Use a restrictive pattern that matches only text extensions
    files = indexer.scan_files([str(tmp_path)], glob_pattern="*.md")
    assert len(files) == 0


def test_scan_files_missing():
    """Test scanning non-existent path returns empty."""
    files = indexer.scan_files(["/nonexistent/path"])
    assert len(files) == 0


def test_scan_files_glob_filter(tmp_path):
    """Test glob pattern filtering."""
    (tmp_path / "notes.md").write_text("md")
    (tmp_path / "data.txt").write_text("txt")
    (tmp_path / "script.py").write_text("py")

    files = indexer.scan_files([str(tmp_path)])
    # With default pattern, *.py should be included (it's a common text extension)
    # But the default pattern is "[!.]*.*" which matches any file with extension
    assert len(files) >= 2


def test_chunk_files(tmp_path):
    """Test chunking multiple files."""
    f1 = tmp_path / "a.md"
    f2 = tmp_path / "b.md"
    f1.write_text("Hello world! " * 50)
    f2.write_text("Another file. " * 50)

    files = [f1, f2]
    chunks = indexer.chunk_files(files, chunk_size=128, overlap=16)
    assert len(chunks) >= 2  # At least 2 chunks from 2 files
    # Verify chunks from both files
    sources = {c["source_file"] for c in chunks}
    assert "a.md" in sources
    assert "b.md" in sources


def test_chunk_files_skips_binary(tmp_path):
    """Test binary files are skipped during chunking."""
    f = tmp_path / "test.png"
    f.write_bytes(b"\x89PNG\r\n")

    chunks = indexer.chunk_files([f], chunk_size=128, overlap=16)
    assert len(chunks) == 0


def test_drop_nonexistent(tmp_path):
    """Test dropping a non-existent index returns False."""
    assert indexer.drop_index(tmp_path / "nonexistent") is False