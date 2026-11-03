"""Timing maths: the part that must never lie."""

from __future__ import annotations

import pytest

from commutecrafter.timing import (
    DEFAULT_PROFILE,
    ITEM_OVERHEAD_SECONDS,
    LISTEN_WPM,
    READ_WPM,
    PacingProfile,
    clamp_minutes,
    estimate_seconds,
    format_duration,
    words_for_seconds,
    wpm_for_mode,
)


def test_estimate_seconds_exact_minute():
    assert estimate_seconds(READ_WPM, READ_WPM) == 60
    assert estimate_seconds(LISTEN_WPM, LISTEN_WPM) == 60


def test_estimate_seconds_rounds_up():
    assert estimate_seconds(1, READ_WPM) == 1
    assert estimate_seconds(231, 230) == 61


def test_estimate_seconds_zero_words_is_zero():
    assert estimate_seconds(0, READ_WPM) == 0
    assert estimate_seconds(-5, READ_WPM) == 0


def test_estimate_seconds_adds_overhead():
    base = estimate_seconds(460, READ_WPM)
    assert estimate_seconds(460, READ_WPM, ITEM_OVERHEAD_SECONDS) == base + ITEM_OVERHEAD_SECONDS


def test_estimate_seconds_rejects_bad_wpm():
    with pytest.raises(ValueError):
        estimate_seconds(100, 0)


def test_words_for_seconds_is_inverse():
    seconds = 300
    words = words_for_seconds(seconds, READ_WPM)
    assert abs(estimate_seconds(words, READ_WPM) - seconds) <= 1


def test_listening_is_slower_than_reading():
    assert estimate_seconds(1000, LISTEN_WPM) > estimate_seconds(1000, READ_WPM)


def test_wpm_for_mode():
    assert wpm_for_mode("listen") == LISTEN_WPM
    assert wpm_for_mode("audio") == LISTEN_WPM
    assert wpm_for_mode("read") == READ_WPM
    assert wpm_for_mode("anything else") == READ_WPM


def test_clamp_minutes_bounds():
    assert clamp_minutes(-3) == 2.0
    assert clamp_minutes(0) == 2.0
    assert clamp_minutes(9999) == 240.0
    assert clamp_minutes(22) == 22.0
    assert clamp_minutes("17.5") == 17.5


def test_clamp_minutes_rejects_garbage():
    with pytest.raises(ValueError):
        clamp_minutes("soon")
    with pytest.raises(ValueError):
        clamp_minutes(float("nan"))


def test_format_duration():
    assert format_duration(0) == "0:00"
    assert format_duration(65) == "1:05"
    assert format_duration(3725) == "1:02:05"


def test_pacing_budgets_sum_to_total():
    for total in (120, 480, 1320, 3600, 7200, 14401):
        budgets = DEFAULT_PROFILE.budgets(total)
        assert sum(budgets.values()) == total
        assert set(budgets) == {"warm-up", "core", "wind-down"}


def test_core_gets_the_biggest_slice():
    budgets = DEFAULT_PROFILE.budgets(3600)
    assert budgets["core"] > budgets["warm-up"]
    assert budgets["core"] > budgets["wind-down"]


def test_pacing_profile_rejects_bad_shares():
    with pytest.raises(ValueError):
        PacingProfile(warmup=0.5, core=0.5, winddown=0.5)
