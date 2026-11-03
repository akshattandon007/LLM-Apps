"""Persistence: history and the 'already served' memory."""

from __future__ import annotations

import time

from commutecrafter.planner import build_plan
from commutecrafter.store import Store, default_db_path


def test_schema_created(tmp_path):
    store = Store(tmp_path / "nested" / "db.sqlite")
    assert store.path.exists()
    assert store.stats()["plans"] == 0


def test_record_and_history(corpus_items):
    store = Store()
    plan = build_plan(corpus_items, 20)
    plan_id = store.record_plan(plan)
    assert plan_id == 1
    rows = store.history(limit=5)
    assert len(rows) == 1
    assert rows[0]["minutes"] == plan.minutes
    assert len(rows[0]["items"]) == len(plan.scheduled_items)


def test_history_order_is_newest_first(corpus_items):
    store = Store()
    store.record_plan(build_plan(corpus_items, 12))
    store.record_plan(build_plan(corpus_items, 30))
    rows = store.history(limit=5)
    assert rows[0]["minutes"] > rows[1]["minutes"]


def test_mark_served_and_recently_served(corpus_items):
    store = Store()
    plan = build_plan(corpus_items, 22)
    tuples = [(s.item.url, s.item.title, s.item.source) for s in plan.scheduled_items]
    assert store.mark_served(tuples) == len(tuples)
    served = store.recently_served(days=14)
    assert {t[0].lower() for t in tuples} <= served


def test_recently_served_respects_window(corpus_items):
    store = Store()
    store.mark_served([("https://old.example", "Old", "wikipedia")])
    # Age the row past the window.
    import sqlite3

    with sqlite3.connect(store.path) as conn:
        conn.execute("UPDATE served SET served_at = ?", (time.time() - 40 * 86400,))
    assert store.recently_served(days=14) == set()


def test_mark_served_is_idempotent():
    store = Store()
    store.mark_served([("https://x/1", "One", "wikipedia")])
    store.mark_served([("https://x/1", "One", "wikipedia")])
    assert store.stats()["served_items"] == 1


def test_mark_served_empty_is_noop():
    assert Store().mark_served([]) == 0


def test_clear_wipes_everything(corpus_items):
    store = Store()
    store.record_plan(build_plan(corpus_items, 15))
    store.mark_served([("https://x/1", "One", "wikipedia")])
    store.clear()
    assert store.stats() == {"plans": 0, "served_items": 0, "db": store.stats()["db"]}
    assert store.history() == []


def test_default_db_path_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("COMMUTECRAFTER_DB", str(tmp_path / "custom.db"))
    assert default_db_path() == tmp_path / "custom.db"


def test_served_memory_changes_the_plan(corpus_items):
    store = Store()
    first = build_plan(corpus_items, 25, exclude_urls=store.recently_served())
    store.mark_served([(s.item.url, s.item.title, s.item.source) for s in first.scheduled_items])
    second = build_plan(corpus_items, 25, exclude_urls=store.recently_served())
    assert not ({s.item.url for s in first.scheduled_items} & {s.item.url for s in second.scheduled_items})
