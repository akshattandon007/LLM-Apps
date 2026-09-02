"""Smoke tests for Subscription Slayer."""

import json
import os
import sys
from datetime import date, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.canceller import get_cancellation_info, list_known_merchants
from src.categorizer import (
    categorize,
    detect_recurring,
    estimate_annual_cost,
    identify_unused,
    track_trials,
)
from src.merchant_db import MERCHANT_DB
from src.models import CategorizedSub, Category, Charge, Frequency, Subscription
from src.scanner import scan_statements, scan_statement_text


# ── Scanner Tests ──────────────────────────────────────────────────────────


def test_scan_csv(sample_csv_path):
    """Smoke: scan a basic CSV and get charges back."""
    result = scan_statements(sample_csv_path)
    assert result.total_transactions > 0
    assert len(result.errors) == 0
    assert result.total_transactions >= 19


def test_scan_csv_errors(tmp_path):
    """Graceful handling of missing file."""
    result = scan_statements(str(tmp_path / "nonexistent.csv"))
    assert result.total_transactions == 0
    assert len(result.errors) > 0
    assert "not found" in result.errors[0].lower()


def test_scan_empty_csv(tmp_path):
    """Graceful handling of empty CSV."""
    path = tmp_path / "empty.csv"
    path.write_text("")
    result = scan_statements(str(path))
    assert result.total_transactions == 0


def test_scan_multi_column(multi_col_csv_path):
    """Scan multi-column 'Debit/Credit' format."""
    result = scan_statements(multi_col_csv_path)
    assert result.total_transactions >= 3
    assert all(c.amount > 0 for c in result.charges)


def test_scan_csv_text():
    """Scan from raw CSV text."""
    csv_text = "Date,Description,Amount\n2025-01-01,NETFLIX,15.49\n2025-02-01,NETFLIX,15.49"
    result = scan_statement_text(csv_text)
    assert result.total_transactions == 2
    assert result.charges[0].merchant == "netflix"


# ── Merchant resolution ───────────────────────────────────────────────────


def test_scan_merchant_resolution(sample_csv_path):
    """Known merchants should be resolved from description."""
    result = scan_statements(sample_csv_path)
    resolved = [c for c in result.charges if c.merchant is not None]
    assert len(resolved) > 0


# ── Recurring Detection ───────────────────────────────────────────────────


def test_detect_recurring(sample_charges):
    """Recurring charges with 2+ occurrences are detected."""
    subs = detect_recurring(sample_charges)
    assert len(subs) >= 2
    merchants = [s.merchant for s in subs]
    assert "Spotify" in merchants
    assert "Netflix" in merchants


def test_detect_recurring_filters_one_off(sample_charges):
    """Single-occurrence charges should not be flagged."""
    subs = detect_recurring(sample_charges)
    merchants = [s.merchant for s in subs]
    assert "Gas Station" not in merchants
    assert "Grocery Store" not in merchants


def test_detect_frequency_monthly(sample_charges):
    """Monthly recurring charges get frequency=monthly."""
    subs = detect_recurring(sample_charges)
    spotify = next(s for s in subs if s.merchant == "Spotify")
    assert spotify.frequency == Frequency.MONTHLY


# ── Categorizer ───────────────────────────────────────────────────────────


def test_categorize(sample_subscriptions):
    """Subscriptions get assigned categories."""
    cats = categorize(sample_subscriptions)
    assert len(cats) == 3
    categories = {c.category for c in cats}
    assert Category.MUSIC in categories
    assert Category.STREAMING in categories


def test_categorize_annual_cost(sample_subscriptions):
    """Annual costs are calculated correctly."""
    cats = categorize(sample_subscriptions)
    spotify = next(c for c in cats if c.merchant == "Spotify")
    assert spotify.annual_cost == pytest.approx(10.99 * 12)


def test_estimate_annual_cost(sample_categorized):
    """Annual cost summary includes categories and total."""
    summary = estimate_annual_cost(sample_categorized)
    assert "Annual Cost Summary" in summary
    assert "TOTAL" in summary
    expected_total = 131.88 + 185.88 + 95.88 + 131.88
    assert f"{expected_total:.2f}" in summary


def test_estimate_annual_cost_empty():
    """Empty list returns appropriate message."""
    summary = estimate_annual_cost([])
    assert "No subscriptions found" in summary


# ── Identify Unused ───────────────────────────────────────────────────────


def test_identify_unused(sample_categorized):
    """User says they don't use certain subscriptions."""
    user_answers = {"spotify": False, "netflix": True, "disney+": False}
    forgotten = identify_unused(sample_categorized, user_answers)
    assert "Spotify" in forgotten
    assert "Disney+" in forgotten
    assert "Netflix" not in forgotten


def test_identify_unused_none(sample_categorized):
    """All in use => no forgotten."""
    user_answers = {s.merchant.lower(): True for s in sample_categorized}
    forgotten = identify_unused(sample_categorized, user_answers)
    assert len(forgotten) == 0


# ── Trial Tracking ────────────────────────────────────────────────────────


def test_track_trials_categorized():
    """Trials that are about to convert are flagged."""
    subs = [
        CategorizedSub(
            merchant="Duolingo Plus", amount=6.99, frequency=Frequency.MONTHLY,
            category=Category.EDUCATION, annual_cost=83.88,
            is_trial=True, trial_end=date.today() + timedelta(days=1),
        ),
        CategorizedSub(
            merchant="Calm", amount=14.99, frequency=Frequency.MONTHLY,
            category=Category.FITNESS, annual_cost=179.88,
            is_trial=True, trial_end=date.today() - timedelta(days=1),
        ),
    ]
    warnings = track_trials(subs)
    assert len(warnings) == 2
    assert "CONVERTED" in warnings[0].upper() or "CONVERTED" in warnings[1].upper()


def test_track_trials_no_trials():
    """No active trials => appropriate message."""
    subs = [
        CategorizedSub(
            merchant="Netflix", amount=15.49, frequency=Frequency.MONTHLY,
            category=Category.STREAMING, annual_cost=185.88,
        ),
    ]
    warnings = track_trials(subs)
    assert any("No active trials" in w for w in warnings)


# ── Canceller ─────────────────────────────────────────────────────────────


def test_get_cancellation_info_known():
    """Known service returns cancellation details."""
    info = get_cancellation_info("netflix")
    assert "Netflix" in info
    assert "cancel" in info.lower()
    assert "netflix.com" in info


def test_get_cancellation_info_unknown():
    """Unknown service returns helpful message."""
    info = get_cancellation_info("nonexistent_service_xyz")
    assert "not found" in info.lower()
    assert "spotify" in info


def test_get_cancellation_info_alias():
    """Alias name resolves correctly."""
    info = get_cancellation_info("disney plus")
    assert "Disney+" in info


def test_known_merchants_count():
    """At least 20 merchants in database."""
    merchants = list_known_merchants()
    assert len(merchants) >= 20


def test_all_merchants_have_cancellation_url():
    """Every merchant in the DB should have a cancellation URL."""
    for name, info in MERCHANT_DB.items():
        assert info.cancellation_url, f"{name} missing cancellation_url"


# ── Model Tests ───────────────────────────────────────────────────────────


def test_charge_model():
    """Charge model creates and serializes correctly."""
    c = Charge(date=date(2025, 1, 1), description="Test", amount=9.99)
    assert c.amount == 9.99
    assert c.merchant is None


def test_subscription_model():
    """Subscription model creates correctly."""
    s = Subscription(
        merchant="Spotify", amount=10.99, frequency=Frequency.MONTHLY,
        last_seen=date(2025, 3, 1),
    )
    assert s.occurrences == 1
    assert s.frequency == Frequency.MONTHLY


# ── Integration: Full Pipeline ────────────────────────────────────────────


def test_full_pipeline(sample_csv_path):
    """End-to-end: scan -> detect -> categorize -> cost estimate."""
    result = scan_statements(sample_csv_path)
    assert result.total_transactions >= 19
    assert len(result.errors) == 0

    subs = detect_recurring(result.charges)
    assert len(subs) >= 2

    cats = categorize(subs)
    assert len(cats) >= 2
    assert all(c.annual_cost > 0 for c in cats)

    summary = estimate_annual_cost(cats)
    assert "Annual Cost Summary" in summary
    assert "TOTAL" in summary


# ── Server Import ─────────────────────────────────────────────────────────


def test_server_imports():
    """Server module imports cleanly."""
    for key in list(sys.modules.keys()):
        if "server" in key or "mcp.server" in key:
            del sys.modules[key]
    from server import mcp
    assert mcp is not None
    assert mcp.name == "subscription-slayer"