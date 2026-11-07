"""Tests for ClipRef utility functions."""

import pytest
from pathlib import Path

from clipref import utils


def test_is_binary():
    """Verify binary extension detection."""
    assert utils.is_binary(Path("image.png"))
    assert utils.is_binary(Path("doc.pdf"))
    assert utils.is_binary(Path("archive.zip"))
    assert not utils.is_binary(Path("notes.md"))
    assert not utils.is_binary(Path("script.py"))
    assert not utils.is_binary(Path("readme.txt"))
    assert not utils.is_binary(Path("index.html"))


def test_read_file_safe(tmp_path):
    """Test safe file reading with UTF-8."""
    f = tmp_path / "test.md"
    f.write_text("Hello, world!", encoding="utf-8")
    assert utils.read_file_safe(f) == "Hello, world!"


def test_read_file_safe_binary(tmp_path):
    """Test that binary files return None."""
    f = tmp_path / "image.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n")
    assert utils.read_file_safe(f) is None


def test_read_file_safe_missing(tmp_path):
    """Test missing file returns None."""
    f = tmp_path / "nonexistent.md"
    assert utils.read_file_safe(f) is None


def test_hash_file(tmp_path):
    """Test SHA-256 file hashing."""
    f = tmp_path / "test.txt"
    f.write_text("content")
    h1 = utils.hash_file(f)
    assert len(h1) == 64  # SHA-256 hex digest
    assert all(c in "0123456789abcdef" for c in h1)


def test_chunk_text_basic():
    """Test basic text chunking."""
    text = "Hello world. " * 100
    chunks = list(utils.chunk_text(text, Path("test.md"), "abc123", chunk_size=128, overlap=16))
    assert len(chunks) > 1
    assert all(c["source_file"] == "test.md" for c in chunks)
    assert all(c["file_hash"] == "abc123" for c in chunks)


def test_chunk_text_small():
    """Test that small text produces exactly one chunk."""
    text = "Short text."
    chunks = list(utils.chunk_text(text, Path("short.md"), "def456", chunk_size=512, overlap=64))
    assert len(chunks) == 1
    assert chunks[0]["text"] == "Short text."


def test_chunk_text_empty():
    """Test empty text produces no chunks."""
    chunks = list(utils.chunk_text("", Path("empty.md"), "aaa", chunk_size=128, overlap=16))
    assert len(chunks) == 0


def test_hash_path(tmp_path):
    """Test path-based hashing (idempotent for the same file)."""
    f = tmp_path / "test.txt"
    f.write_text("hello")
    h1 = utils.hash_path(f)
    h2 = utils.hash_path(f)
    assert h1 == h2


def test_chunk_id():
    """Test chunk ID determinism."""
    from clipref.utils import chunk_id
    p = Path("/tmp/test.md")
    cid1 = chunk_id(p, 0, "hash123")
    cid2 = chunk_id(p, 0, "hash123")
    assert cid1 == cid2
    # Different chunk index = different ID
    cid3 = chunk_id(p, 1, "hash123")
    assert cid1 != cid3
    assert len(cid1) == 64


def test_get_env_no_file():
    """Test env var reading when no .clipref.env exists."""
    assert utils.get_env("NONEXISTENT_VAR") == ""


def test_get_env_from_file(tmp_path, monkeypatch):
    """Test env var reading from .clipref.env."""
    env_file = tmp_path / ".clipref.env"
    env_file.write_text('CLIPREF_MODEL="custom-model"\n')
    monkeypatch.chdir(tmp_path)
    assert utils.get_env("CLIPREF_MODEL") == "custom-model"


def test_now_iso():
    """Test ISO timestamp format."""
    ts = utils.now_iso()
    assert "T" in ts
    assert ts.endswith("+00:00") or "+00:00" in ts or ts.endswith("Z")