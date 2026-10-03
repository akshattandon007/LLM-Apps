"""Tests for the Verification Agent."""

import csv
import io

from subs_sleuth.models import Subscription, StatementLine
from subs_sleuth.verify_agent import (
    verify_subscriptions,
    verify_demo,
    parse_statement_csv,
    _normalize_columns,
    _match_score,
)


class TestVerifyAgent:
    def test_verify_demo_returns_reports(self):
        reports = verify_demo()
        assert len(reports) > 0
        for r in reports:
            assert r.found_on_statement is not None

    def test_verify_demo_matches(self):
        reports = verify_demo()
        found = [r for r in reports if r.found_on_statement]
        assert len(found) > 0

    def test_verify_no_match(self):
        subs = [Subscription(merchant="RandomUnmatchedService", amount=99.99)]
        lines = [
            StatementLine(date="2025-01-15", description="Netflix", amount=-15.99)
        ]
        reports = verify_subscriptions(subs, lines)
        assert len(reports) == 1
        assert not reports[0].found_on_statement

    def test_verify_exact_match(self):
        subs = [Subscription(merchant="Netflix", amount=15.99)]
        lines = [
            StatementLine(date="2025-01-15", description="NETFLIX.COM", amount=-15.99)
        ]
        reports = verify_subscriptions(subs, lines)
        assert len(reports) == 1
        assert reports[0].found_on_statement
        assert reports[0].match_confidence == "high"

    def test_parse_statement_csv(self):
        csv_text = "Date,Description,Amount\n2025-01-15,NETFLIX.COM,15.99\n2025-01-16,SPOTIFY,11.99\n"
        lines = parse_statement_csv(csv_text)
        assert len(lines) == 2
        assert lines[0].description == "NETFLIX.COM"
        assert lines[0].amount == 15.99  # abs()

    def test_parse_statement_csv_with_header_variants(self):
        csv_text = "Transaction Date,Merchant,Charges\n2025-01-15,Netflix,$15.99\n"
        lines = parse_statement_csv(csv_text)
        assert len(lines) == 1
        assert lines[0].description == "Netflix"
        assert lines[0].amount == 15.99

    def test_normalize_columns(self):
        columns = ["Transaction Date", "Merchant", "Amount"]
        mapping = _normalize_columns(columns)
        assert mapping.get("date") == "Transaction Date"
        assert mapping.get("description") == "Merchant"
        assert mapping.get("amount") == "Amount"

    def test_normalize_columns_no_match(self):
        mapping = _normalize_columns(["Foo", "Bar", "Baz"])
        assert mapping == {}

    def test_match_score_exact(self):
        sub = Subscription(merchant="Netflix", amount=15.99)
        line = StatementLine(date="2025-01-15", description="NETFLIX.COM", amount=-15.99)
        score = _match_score(sub, line)
        assert score >= 0.9  # name match + exact amount

    def test_match_score_partial(self):
        sub = Subscription(merchant="Netflix", amount=15.99)
        line = StatementLine(date="2025-01-15", description="NETFLIX PREMIUM", amount=-14.99)
        score = _match_score(sub, line)
        assert score > 0  # partial match
        assert score < 0.9  # not perfect

    def test_match_score_no_match(self):
        sub = Subscription(merchant="Netflix", amount=15.99)
        line = StatementLine(date="2025-01-15", description="GAS STATION", amount=-45.00)
        score = _match_score(sub, line)
        assert score == 0.0