"""Tests for Renamer — core rename logic."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from renamer.core import (
    _resolve_conflicts,
    preview,
    rename,
    undo,
    _load_manifest,
    MANIFEST_FILE,
    MANIFEST_DIR,
)


def _make_files(dirpath: Path, names: list[str]) -> list[Path]:
    paths = []
    for name in names:
        p = dirpath / name
        p.write_text(f"content of {name}")
        paths.append(p)
    return paths


class TestApplyRenameRule:
    """Tests the regex substitution logic (indirectly via preview/rename)."""

    def test_basic_regex(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _make_files(d, ["report_2024.pdf", "report_2025.pdf"])
            results = preview(str(d), r"report_(\d{4})", r"summary_\1")
            assert len(results) == 2
            assert results[0][1].name == "summary_2024.pdf"
            assert results[1][1].name == "summary_2025.pdf"

    def test_counter_token_default(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _make_files(d, ["img1.png", "img2.png", "img3.png"])
            results = preview(str(d), r"img\d+", r"photo_{n}")
            names = {r[1].name for r in results}
            assert "photo_1.png" in names
            assert "photo_2.png" in names
            assert "photo_3.png" in names

    def test_counter_token_padded(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _make_files(d, ["a.txt", "b.txt"])
            results = preview(str(d), r"\w+", r"file_{n:3}")
            names = {r[1].name for r in results}
            assert "file_001.txt" in names
            assert "file_002.txt" in names

    def test_start_num(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _make_files(d, ["x.txt", "y.txt"])
            results = preview(str(d), r"\w+", r"item_{n}", start_num=10)
            names = {r[1].name for r in results}
            assert "item_10.txt" in names
            assert "item_11.txt" in names

    def test_no_change_skipped(self):
        """Files whose names don't change after substitution should be skipped."""
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _make_files(d, ["keep.txt", "change_me.txt"])
            results = preview(str(d), r"keep", r"kept")  # keep.txt → kept.txt
            assert len(results) == 1
            assert results[0][1].name == "kept.txt"

    def test_extension_filter(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _make_files(d, ["data.csv", "data.txt"])
            results = preview(str(d), r"\w+", r"renamed", file_ext="txt")
            assert len(results) == 1
            assert results[0][1].name == "renamed.txt"


class TestResolveConflicts:
    def test_no_conflicts(self):
        pairs = [
            (Path("/a/foo.txt"), "bar.txt"),
            (Path("/a/baz.txt"), "qux.txt"),
        ]
        resolved = _resolve_conflicts(pairs)
        assert len(resolved) == 2

    def test_duplicate_target_names(self):
        pairs = [
            (Path("/a/foo.txt"), "out.txt"),
            (Path("/a/bar.txt"), "out.txt"),
        ]
        resolved = _resolve_conflicts(pairs)
        assert len(resolved) == 2
        names = {r[1].name for r in resolved}
        assert "out.txt" in names
        assert any("out" in r[1].stem and r[1].suffix == ".txt" for r in resolved)


class TestRename:
    def test_rename_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _make_files(d, ["old_name.txt"])
            results = rename(str(d), r"old", r"new", dry_run=True)
            assert len(results) == 1
            assert results[0][1].name == "new_name.txt"
            assert (d / "old_name.txt").exists()
            assert not (d / "new_name.txt").exists()

    def test_rename_actual(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _make_files(d, ["old_name.txt"])
            results = rename(str(d), r"old", r"new")
            assert len(results) == 1
            assert not (d / "old_name.txt").exists()
            assert (d / "new_name.txt").exists()

    def test_rename_multi_file(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _make_files(d, ["a.txt", "b.txt", "c.txt"])
            results = rename(str(d), r"", r"file_{n}")
            assert len(results) == 3

    def test_manifest_saved(self):
        # Clean up any prior manifest
        if MANIFEST_FILE.exists():
            MANIFEST_FILE.unlink()
        if MANIFEST_DIR.exists():
            MANIFEST_DIR.rmdir()

        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _make_files(d, ["alpha.txt", "beta.txt"])
            rename(str(d), r"\w+", r"file_{n}")
            manifest = _load_manifest()
            assert len(manifest) == 1
            assert len(manifest[0]["changes"]) == 2


class TestUndo:
    def test_undo_reverts(self):
        # Clean up prior manifest
        if MANIFEST_FILE.exists():
            MANIFEST_FILE.unlink()

        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _make_files(d, ["a.txt", "b.txt"])
            rename(str(d), r"(\w)", r"prefix_\1")
            assert (d / "prefix_a.txt").exists()
            assert not (d / "a.txt").exists()

            undo(limit=1)
            assert (d / "a.txt").exists()
            assert not (d / "prefix_a.txt").exists()

    def test_undo_empty_manifest(self):
        if MANIFEST_FILE.exists():
            MANIFEST_FILE.unlink()
        result = undo(limit=1)
        assert result == 0


class TestPreviewOutput:
    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            results = preview(str(d), r".*", r"new")
            assert results == []

    def test_none_match(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _make_files(d, ["keep.txt"])
            results = preview(str(d), r"nomatch", r"new")
            assert results == []

    def test_recursive(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            sub = d / "sub"
            sub.mkdir()
            _make_files(d, ["root.txt"])
            _make_files(sub, ["nested.txt"])
            results = preview(str(d), r"", r"renamed_", recursive=True)
            assert len(results) == 2