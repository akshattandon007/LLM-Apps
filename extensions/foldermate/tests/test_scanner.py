"""Tests for FolderMate scanner."""

import pytest
from pathlib import Path
from datetime import datetime
from foldermate.config import FolderMateConfig
from foldermate.scanner import scan_directory, _get_category


class TestGetCategory:
    def test_pdf_is_document(self):
        assert _get_category(".pdf") == "Documents"

    def test_jpg_is_image(self):
        assert _get_category(".jpg") == "Images"

    def test_mp3_is_audio(self):
        assert _get_category(".mp3") == "Audio"

    def test_mp4_is_video(self):
        assert _get_category(".mp4") == "Video"

    def test_zip_is_archive(self):
        assert _get_category(".zip") == "Archives"

    def test_py_is_code(self):
        assert _get_category(".py") == "Code"

    def test_exe_is_installer(self):
        assert _get_category(".exe") == "Installers"

    def test_unknown_ext_is_others(self):
        assert _get_category(".xyz") == "Others"

    def test_case_insensitive(self):
        assert _get_category(".PDF") == "Documents"


class TestScanDirectory:
    def test_no_files_in_empty_dir(self, tmp_path):
        config = FolderMateConfig(source_dir=tmp_path)
        files = scan_directory(config)
        assert len(files) == 0

    def test_finds_single_file(self, tmp_path):
        (tmp_path / "test.txt").write_text("hello")
        config = FolderMateConfig(source_dir=tmp_path)
        files = scan_directory(config)
        assert len(files) == 1
        assert files[0].name == "test.txt"
        assert files[0].category == "Documents"

    def test_skips_hidden_files(self, tmp_path):
        (tmp_path / ".hidden.txt").write_text("secret")
        (tmp_path / "visible.txt").write_text("hello")
        config = FolderMateConfig(source_dir=tmp_path)
        files = scan_directory(config)
        assert all(not f.name.startswith(".") for f in files)
        assert len(files) == 1
        assert files[0].name == "visible.txt"

    def test_includes_hidden_when_flag_set(self, tmp_path):
        (tmp_path / ".hidden.txt").write_text("secret")
        (tmp_path / "visible.txt").write_text("hello")
        config = FolderMateConfig(source_dir=tmp_path, include_hidden=True)
        files = scan_directory(config)
        assert len(files) == 2

    def test_raises_on_nonexistent_dir(self):
        config = FolderMateConfig(source_dir=Path("/nonexistent-path-12345"))
        with pytest.raises(FileNotFoundError):
            scan_directory(config)

    def test_categorizes_correctly(self, tmp_path):
        (tmp_path / "doc.pdf").write_text("pdf")
        (tmp_path / "img.jpg").write_text("img")
        (tmp_path / "song.mp3").write_text("song")
        config = FolderMateConfig(source_dir=tmp_path)
        files = scan_directory(config)
        categories = {f.name: f.category for f in files}
        assert categories["doc.pdf"] == "Documents"
        assert categories["img.jpg"] == "Images"
        assert categories["song.mp3"] == "Audio"