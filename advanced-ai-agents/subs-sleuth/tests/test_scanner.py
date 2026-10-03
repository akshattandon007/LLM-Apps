"""Tests for the Scanner Agent."""

import json
from unittest.mock import patch

from subs_sleuth.scanner_agent import scan_demo, _heuristic_extract
from subs_sleuth.models import Subscription


class TestScannerAgent:
    def test_scan_demo_returns_report(self):
        report = scan_demo()
        assert report.total_found > 0
        assert report.email_count_checked > 0
        assert len(report.subscriptions) == report.total_found

    def test_scan_demo_contains_known_services(self):
        report = scan_demo()
        merchants = [s.merchant for s in report.subscriptions]
        assert "Netflix" in merchants
        assert "Spotify Premium" in merchants
        assert "Amazon Prime" in merchants
        assert "ChatGPT Plus" in merchants

    def test_scan_demo_subscriptions_have_amounts(self):
        report = scan_demo()
        for sub in report.subscriptions:
            assert sub.amount is not None
            assert sub.amount > 0

    def test_heuristic_extract_netflix(self):
        result = _heuristic_extract({
            "subject": "Your Netflix receipt for this month",
            "sender": "info@netflix.com",
            "body_snippet": "Thank you for your payment",
        })
        assert result is not None
        assert result.merchant == "Netflix"
        assert result.billing_url == "https://www.netflix.com/account"

    def test_heuristic_extract_spotify(self):
        result = _heuristic_extract({
            "subject": "Your Spotify Premium payment was received",
            "sender": "no-reply@spotify.com",
            "body_snippet": "Premium subscription renewed",
        })
        assert result is not None
        assert result.merchant == "Spotify Premium"

    def test_heuristic_extract_unknown(self):
        result = _heuristic_extract({
            "subject": "Your order from Amazon was shipped",
            "sender": "orders@amazon.com",
            "body_snippet": "Your package is on its way",
        })
        # This is an order, not a subscription — no match expected
        assert result is None

    def test_heuristic_extract_empty(self):
        result = _heuristic_extract({"subject": "", "sender": "", "body_snippet": ""})
        assert result is None

    def test_heuristic_extract_generic_receipt(self):
        result = _heuristic_extract({
            "subject": "Your Monthly Payment Receipt — CloudSync Pro",
            "sender": "billing@cloudsync.com",
            "body_snippet": "Thank you for your payment",
        })
        assert result is not None
        assert result.merchant == "CloudSync Pro"