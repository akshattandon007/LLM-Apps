"""Date extraction unit tests — all deterministic via explicit `today`."""
from datetime import date

from schoolsift.dates import extract_dates


def test_month_day_event():
    hits = extract_dates("The science fair is October 14.", today=date(2026, 10, 1))
    assert [h.iso for h in hits] == ["2026-10-14"]
    assert hits[0].kind == "event"


def test_abbreviated_month():
    hits = extract_dates("Book fair Oct 14.", today=date(2026, 10, 1))
    assert hits[0].iso == "2026-10-14"


def test_year_rollover_past_date_goes_next_year():
    hits = extract_dates("The winter concert is December 15.", today=date(2026, 12, 20))
    assert hits[0].iso == "2027-12-15"


def test_deadline_kind_detected():
    hits = extract_dates("Permission slips are due by 10/28/2026.", today=date(2026, 10, 1))
    assert (hits[0].iso, hits[0].kind) == ("2026-10-28", "deadline")


def test_dd_mm_heuristic():
    hits = extract_dates("Form due 31/12/2026.", today=date(2026, 10, 1))
    assert hits[0].iso == "2026-12-31"


def test_iso_date():
    hits = extract_dates("Early dismissal on 2026-11-03.", today=date(2026, 10, 1))
    assert hits[0].iso == "2026-11-03"


def test_relative_weekday():
    # 2026-10-12 is a Monday → "Friday" resolves to Friday 2026-10-16
    hits = extract_dates("Return the form on Friday.", today=date(2026, 10, 12))
    assert hits[0].iso == "2026-10-16"


def test_next_weekday_skips_current_week():
    hits = extract_dates("Next Wednesday is early release.", today=date(2026, 10, 12))
    assert hits[0].iso == "2026-10-21"


def test_dedupe_repeated_date():
    text = "The fair is October 14. Mark your calendar for October 14 too."
    hits = extract_dates(text, today=date(2026, 10, 1))
    assert [h.iso for h in hits] == ["2026-10-14"]


def test_sorted_chronologically():
    text = "The picnic is October 24. Picture day is November 3. Book fair is October 14."
    hits = extract_dates(text, today=date(2026, 10, 1))
    assert [h.iso for h in hits] == ["2026-10-14", "2026-10-24", "2026-11-03"]


def test_month_day_and_weekday_dedupe_same_date():
    # "Saturday, October 24" produces both a month-day and a weekday hit for
    # the same date — dedupe must collapse them into one.
    text = "The Fall Family Picnic is scheduled for Saturday, October 24 at the park."
    hits = extract_dates(text, today=date(2026, 10, 12))
    assert [h.iso for h in hits] == ["2026-10-24"]