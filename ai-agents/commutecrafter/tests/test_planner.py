"""Planner behaviour: fits, diversity, determinism, degradation."""

from __future__ import annotations

import pytest

from commutecrafter.models import ContentItem, SEGMENT_ORDER
from commutecrafter.planner import MAX_PER_SOURCE, MIN_PARTIAL_FRACTION, build_plan
from commutecrafter.timing import LISTEN_WPM, READ_WPM

WINDOWS = [8, 11, 15, 22, 30, 45, 60]


@pytest.mark.parametrize("minutes", WINDOWS)
def test_plan_fits_window(corpus_items, minutes):
    plan = build_plan(corpus_items, minutes, mode="read")
    assert plan.fits, f"{minutes} min plan off by {plan.delta_seconds}s with {plan.to_dict()}"
    assert plan.total_seconds > 0


@pytest.mark.parametrize("minutes", [12, 22, 40])
def test_listen_plan_also_fits(corpus_items, minutes):
    plan = build_plan(corpus_items, minutes, mode="listen")
    assert plan.fits


def test_segments_are_ordered_and_named(corpus_items):
    plan = build_plan(corpus_items, 30)
    names = [s.name for s in plan.segments]
    assert names == [n for n in SEGMENT_ORDER if n in names]
    assert all(s.items for s in plan.segments)


def test_never_leans_on_one_source(corpus_items):
    plan = build_plan(corpus_items, 60)
    counts: dict[str, int] = {}
    for sched in plan.scheduled_items:
        counts[sched.item.source] = counts.get(sched.item.source, 0) + 1
    assert max(counts.values()) <= MAX_PER_SOURCE + 1  # padding may add one extra


def test_no_duplicate_items(corpus_items):
    plan = build_plan(corpus_items, 45)
    titles = [s.item.title for s in plan.scheduled_items]
    urls = [s.item.url for s in plan.scheduled_items]
    assert len(titles) == len(set(titles))
    assert len(urls) == len(set(urls))


def test_excluded_urls_are_never_used(corpus_items):
    banned = {corpus_items[0].url, corpus_items[1].url, corpus_items[5].url}
    plan = build_plan(corpus_items, 30, exclude_urls=banned)
    assert not ({s.item.url for s in plan.scheduled_items} & banned)


def test_warmup_items_are_short(corpus_items):
    plan = build_plan(corpus_items, 45)
    warm = next((s for s in plan.segments if s.name == "warm-up"), None)
    if warm:
        assert all(i.seconds <= 5 * 60 for i in warm.items)


def test_partial_fractions_are_sane(corpus_items):
    for minutes in WINDOWS:
        plan = build_plan(corpus_items, minutes)
        for sched in plan.scheduled_items:
            assert 0 < sched.fraction <= 1.0
            if sched.partial:
                assert sched.fraction >= MIN_PARTIAL_FRACTION
            assert sched.seconds > 0


def test_deterministic_for_same_input(corpus_items):
    first = build_plan(corpus_items, 24)
    second = build_plan(corpus_items, 24)
    assert [s.item.url for s in first.scheduled_items] == [s.item.url for s in second.scheduled_items]
    assert first.total_seconds == second.total_seconds


def test_listen_mode_plans_less_text(corpus_items):
    read = build_plan(corpus_items, 30, mode="read")
    listen = build_plan(corpus_items, 30, mode="listen")
    read_words = sum(s.item.words for s in read.scheduled_items)
    listen_words = sum(s.item.words for s in listen.scheduled_items)
    assert listen_words < read_words


def test_empty_pool_degrades_without_crashing():
    plan = build_plan([], 20)
    assert plan.total_seconds == 0
    assert plan.fits is False
    assert plan.segments == []


def test_tiny_pool_still_returns_best_effort():
    one = ContentItem(title="Only item", source="wikipedia", url="u1", words=1200, category="culture")
    plan = build_plan([one], 20)
    assert len(plan.scheduled_items) == 1
    assert plan.scheduled_items[0].fraction <= 1.0


def test_tolerance_is_respected_for_custom_value(corpus_items):
    plan = build_plan(corpus_items, 17, tolerance=20)
    assert abs(plan.delta_seconds) <= 20


def test_zero_word_items_are_ignored(corpus_items):
    junk = ContentItem(title="Empty", source="wikipedia", url="junk", words=0)
    plan = build_plan([junk] + corpus_items, 20)
    assert "Empty" not in [s.item.title for s in plan.scheduled_items]


def test_weather_is_carried_into_plan(corpus_items):
    weather = {"city": "London", "temp_c": 4.0, "precipitation_mm": 0.0, "code": 3}
    plan = build_plan(corpus_items, 20, weather=weather, transport="walk")
    assert plan.weather == weather
    assert plan.transport == "walk"


def test_mode_is_recorded(corpus_items):
    plan = build_plan(corpus_items, 20, mode="listen")
    assert plan.mode == "listen"
    assert plan.to_dict()["mode"] == "listen"


def test_words_per_minute_constant_is_used(corpus_items):
    """A 20 minute read plan should hold roughly 20 * READ_WPM words."""
    plan = build_plan(corpus_items, 20, mode="read", tolerance=90)
    total_words = sum(int(s.item.words * s.fraction) for s in plan.scheduled_items)
    expected = 20 * READ_WPM
    assert abs(total_words - expected) / expected < 0.25


def test_listen_uses_listen_wpm(corpus_items):
    plan = build_plan(corpus_items, 20, mode="listen", tolerance=90)
    total_words = sum(int(s.item.words * s.fraction) for s in plan.scheduled_items)
    expected = 20 * LISTEN_WPM
    assert abs(total_words - expected) / expected < 0.25
