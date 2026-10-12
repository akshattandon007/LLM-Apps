"""End-to-end CLI tests: index → ask → dates → list → clear."""
from pathlib import Path

import pytest

from schoolsift.cli import main


def test_cli_full_flow(tmp_path: Path, sample_folder: Path, capsys):
    store = tmp_path / "idx.json"

    main(["index", str(sample_folder), "--store", str(store)])
    out = capsys.readouterr().out
    assert "3 document(s)" in out
    assert store.exists()

    main(["list", "--store", str(store)])
    out = capsys.readouterr().out
    assert "newsletter-october" in out
    assert "permission-slip-science-fair" in out
    assert "pta-notes" in out

    main(["ask", "when is the science fair", "--store", str(store)])
    out = capsys.readouterr().out
    assert "Science Fair" in out
    assert "permission-slip-science-fair" in out

    main(["dates", "when is the science fair", "--store", str(store)])
    out = capsys.readouterr().out
    assert "October 28" in out  # context sentence text (year-independent)
    assert "November 20" in out

    main(["clear", "--store", str(store)])
    out = capsys.readouterr().out
    assert "Removed index" in out
    assert not store.exists()


def test_cli_ask_without_index_errors(tmp_path: Path, capsys):
    with pytest.raises(SystemExit) as exc:
        main(["ask", "when is the science fair", "--store", str(tmp_path / "none.json")])
    assert exc.value.code == 1
    out = capsys.readouterr().err
    assert "No index found" in out


def test_cli_index_missing_folder_errors(tmp_path: Path, capsys):
    with pytest.raises(SystemExit) as exc:
        main(["index", str(tmp_path / "does-not-exist"), "--store", str(tmp_path / "x.json")])
    assert exc.value.code == 1
    out = capsys.readouterr().err
    assert "Not a folder" in out