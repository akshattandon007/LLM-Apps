"""CLI end-to-end on the offline corpus (no network)."""

from __future__ import annotations

import json

import pytest

from commutecrafter.cli import main


def run(capsys, argv):
    code = main(argv)
    out, err = capsys.readouterr()
    return code, out, err


def test_plan_offline_json_fits(capsys):
    code, out, _ = run(
        capsys,
        ["plan", "--minutes", "18", "--interests", "history,philosophy",
         "--offline", "--json", "--no-cache", "--no-explain"],
    )
    assert code == 0
    payload = json.loads(out)
    assert payload["fits"] is True
    assert payload["item_count"] >= 1
    assert abs(payload["delta_seconds"]) <= payload["tolerance_seconds"]
    assert payload["segments"]
    for segment in payload["segments"]:
        assert segment["name"] in {"warm-up", "core", "wind-down"}
        assert segment["items"]


def test_plan_offline_renders_tables(capsys):
    code, out, _ = run(
        capsys,
        ["plan", "--minutes", "22", "--interests", "history", "--offline",
         "--no-cache", "--no-explain"],
    )
    assert code == 0
    assert "CommuteCrafter" in out
    assert "fits" in out.lower()


def test_plan_respects_explicit_mode(capsys):
    code, out, _ = run(
        capsys,
        ["plan", "--minutes", "14", "--interests", "history", "--offline",
         "--json", "--no-cache", "--no-explain", "--mode", "listen"],
    )
    assert code == 0
    assert json.loads(out)["mode"] == "listen"


def test_plan_transport_implies_mode(capsys):
    code, out, _ = run(
        capsys,
        ["plan", "--minutes", "14", "--interests", "history", "--offline",
         "--json", "--no-cache", "--no-explain", "--transport", "drive"],
    )
    assert code == 0
    assert json.loads(out)["mode"] == "listen"


def test_plan_records_history(capsys):
    run(capsys, ["plan", "--minutes", "12", "--interests", "history",
                 "--offline", "--json", "--no-explain"])
    code, out, _ = run(capsys, ["history"])
    assert code == 0
    assert "Recent plans" in out


def test_plan_writes_served_memory(capsys):
    code, out, _ = run(
        capsys,
        ["plan", "--minutes", "20", "--interests", "history", "--offline",
         "--json", "--no-explain"],
    )
    first = json.loads(out)
    code, out, _ = run(
        capsys,
        ["plan", "--minutes", "20", "--interests", "history", "--offline",
         "--json", "--no-explain"],
    )
    second = json.loads(out)
    first_urls = {i["url"] for s in first["segments"] for i in s["items"]}
    second_urls = {i["url"] for s in second["segments"] for i in s["items"]}
    assert not (first_urls & second_urls)


def test_search_offline_json(capsys):
    code, out, _ = run(capsys, ["search", "history", "--offline", "--json"])
    assert code == 0
    items = json.loads(out)
    assert items
    assert all({"title", "source", "url", "words"} <= set(i) for i in items)


def test_search_source_filter(capsys):
    code, out, _ = run(capsys, ["search", "history", "--offline", "--json", "--source", "arxiv"])
    assert code == 0
    items = json.loads(out)
    assert all(i["source"] == "arxiv" for i in items)


def test_sources_command(capsys):
    code, out, _ = run(capsys, ["sources"])
    assert code == 0
    for name in ("wikipedia", "arxiv", "hackernews", "gutenberg"):
        assert name in out


def test_stats_and_clear(capsys):
    run(capsys, ["plan", "--minutes", "10", "--interests", "history", "--offline", "--json"])
    code, out, _ = run(capsys, ["stats"])
    assert code == 0
    assert "Saved plans" in out
    code, out, _ = run(capsys, ["clear"])
    assert code == 0
    code, out, _ = run(capsys, ["history"])
    assert code == 0


def test_missing_command_exits_nonzero(capsys):
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code != 0


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "commutecrafter" in capsys.readouterr().out.lower()
