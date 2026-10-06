"""Tests for FolderMate organizer."""

import pytest
from pathlib import Path
from datetime import datetime
from foldermate.config import FolderMateConfig
from foldermate.scanner import FileInfo
from foldermate.organizer import plan_moves
from foldermate.undo import UndoLog
from foldermate.organizer import execute_moves


def _make_fileinfo(path: Path, category: str = "Others") -> FileInfo:
    return FileInfo(
        path=path,
        name=path.name,
        extension=path.suffix,
        category=category,
        size_bytes=100,
        modified=datetime(2025, 6, 15, 10, 0, 0),
    )


class TestPlanMoves:
    def test_by_type_moves_to_category_dir(self, tmp_path):
        test_file = tmp_path / "report.pdf"
        test_file.write_text("test")
        config = FolderMateConfig(source_dir=tmp_path, strategy="by-type")
        files = [_make_fileinfo(test_file, category="Documents")]
        moves = plan_moves(files, config)
        assert len(moves) == 1
        _, target = moves[0]
        assert "Documents" in str(target)
        assert target.name == "report.pdf"

    def test_by_date_moves_to_date_dir(self, tmp_path):
        test_file = tmp_path / "notes.txt"
        test_file.write_text("test")
        config = FolderMateConfig(source_dir=tmp_path, strategy="by-date")
        files = [_make_fileinfo(test_file)]
        files[0].modified = datetime(2025, 6, 15)
        files[0].category = "Documents"
        moves = plan_moves(files, config)
        assert len(moves) == 1
        _, target = moves[0]
        assert "2025-06" in str(target)

    def test_both_moves_to_category_date(self, tmp_path):
        test_file = tmp_path / "photo.jpg"
        test_file.write_text("test")
        config = FolderMateConfig(source_dir=tmp_path, strategy="both")
        files = [_make_fileinfo(test_file, category="Images")]
        files[0].modified = datetime(2025, 6, 15)
        moves = plan_moves(files, config)
        assert len(moves) == 1
        _, target = moves[0]
        assert "Images" in str(target)
        assert "2025-06" in str(target)

    def test_skips_if_already_in_place(self, tmp_path):
        """If the file is already in the target location, skip it."""
        (tmp_path / "Documents").mkdir()
        test_file = tmp_path / "Documents" / "doc.txt"
        test_file.write_text("test")
        config = FolderMateConfig(source_dir=tmp_path, strategy="by-type")
        files = [_make_fileinfo(test_file, category="Documents")]
        moves = plan_moves(files, config)
        assert len(moves) == 0

    def test_handles_name_conflict(self, tmp_path):
        (tmp_path / "Documents").mkdir()
        (tmp_path / "doc.txt").write_text("original")
        (tmp_path / "Documents" / "doc.txt").write_text("existing")
        config = FolderMateConfig(source_dir=tmp_path, strategy="by-type")
        files = [_make_fileinfo(tmp_path / "doc.txt", category="Documents")]
        moves = plan_moves(files, config)
        assert len(moves) == 1
        _, target = moves[0]
        assert target.name != "doc.txt"  # Should have a counter suffix
        assert "doc_" in target.name


class TestUndoLog:
    def test_log_and_read(self, tmp_path):
        log_path = tmp_path / "undo.log"
        undo = UndoLog(log_path)
        undo.log_move("/src/a.txt", "/dst/a.txt")
        undo.log_move("/src/b.txt", "/dst/b.txt")
        entries = undo.read_log()
        assert len(entries) == 2
        assert entries[0] == ("/src/a.txt", "/dst/a.txt")
        assert entries[1] == ("/src/b.txt", "/dst/b.txt")

    def test_empty_log(self, tmp_path):
        log_path = tmp_path / "nonexistent.log"
        undo = UndoLog(log_path)
        assert undo.read_log() == []

    def test_clear_removes_log(self, tmp_path):
        log_path = tmp_path / "undo.log"
        undo = UndoLog(log_path)
        undo.log_move("/src/a.txt", "/dst/a.txt")
        assert log_path.exists()
        undo.clear()
        assert not log_path.exists()