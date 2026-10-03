"""Tests for SubsSleuth data models."""

from subs_sleuth.models import (
    Subscription,
    CancellationGuide,
    StatementLine,
    VerificationReport,
    ScanReport,
    FullReport,
)


class TestModels:
    def test_subscription_defaults(self):
        sub = Subscription(merchant="Netflix")
        assert sub.merchant == "Netflix"
        assert sub.amount is None
        assert sub.currency == "USD"
        assert sub.frequency == "monthly"
        assert sub.source == "email"

    def test_subscription_with_amount(self):
        sub = Subscription(merchant="Spotify", amount=11.99)
        assert sub.amount == 11.99
        d = sub.to_dict()
        assert d["merchant"] == "Spotify"
        assert d["amount"] == 11.99

    def test_cancellation_guide_defaults(self):
        guide = CancellationGuide(merchant="Netflix")
        assert guide.merchant == "Netflix"
        assert guide.cancellation_method == "website"
        assert guide.difficulty == "medium"
        assert guide.steps == []

    def test_cancellation_guide_to_dict(self):
        guide = CancellationGuide(
            merchant="Netflix",
            cancellation_method="website",
            steps=["Step 1", "Step 2"],
            difficulty="easy",
        )
        d = guide.to_dict()
        assert len(d["steps"]) == 2
        assert d["difficulty"] == "easy"

    def test_statement_line(self):
        line = StatementLine(date="2025-01-15", description="Netflix", amount=-15.99)
        assert line.amount == -15.99
        assert line.category is None

    def test_verification_report(self):
        report = VerificationReport(merchant="Netflix", found_on_statement=True)
        assert report.found_on_statement
        assert report.match_confidence == "low"

    def test_scan_report(self):
        sub = Subscription(merchant="Netflix")
        report = ScanReport(subscriptions=[sub], total_found=1, email_count_checked=10)
        d = report.to_dict()
        assert d["total_found"] == 1
        assert d["email_count_checked"] == 10
        assert len(d["subscriptions"]) == 1

    def test_full_report_json(self):
        sub = Subscription(merchant="Netflix")
        scan = ScanReport(subscriptions=[sub], total_found=1)
        guide = CancellationGuide(merchant="Netflix", steps=["Cancel online"])
        full = FullReport(scan=scan, guides=[guide])
        json_str = full.to_json()
        assert "Netflix" in json_str
        assert "scan" in json_str
        assert "guides" in json_str

    def test_full_report_empty(self):
        full = FullReport()
        d = full.to_dict()
        assert d["guides"] == []
        assert d["verification"] == []
        assert d.get("scan") is None