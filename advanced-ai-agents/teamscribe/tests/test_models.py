"""Tests for TeamScribe data models."""

from teamscribe.models import MeetingRecord, Decision, ActionItem


class TestMeetingRecord:
    def test_create_empty(self):
        r = MeetingRecord(title="Standup", date="2026-11-09")
        assert r.title == "Standup"
        assert r.date == "2026-11-09"
        assert r.participants == []
        assert r.raw_notes == ""

    def test_create_with_fields(self):
        r = MeetingRecord(
            title="Sprint Planning",
            date="2026-11-09",
            participants=["Alice", "Bob"],
            raw_notes="discussed sprint goals",
        )
        assert r.title == "Sprint Planning"
        assert "Alice" in r.participants
        assert r.raw_notes == "discussed sprint goals"

    def test_to_dict_roundtrip(self):
        decisions = [Decision(topic="Tech stack", outcome="Choose Python", rationale="Team consensus")]
        actions = [ActionItem(owner="Alice", description="Write tests", deadline="2026-11-10")]
        r = MeetingRecord(
            title="Architecture Review",
            date="2026-11-08",
            participants=["Alice", "Bob"],
            raw_notes="raw notes here",
            cleaned_notes="cleaned notes here",
            summary="A good meeting",
            key_points=["Point 1", "Point 2"],
            decisions=decisions,
            action_items=actions,
            follow_up_email="Thanks all",
        )
        d = r.to_dict()
        r2 = MeetingRecord.from_dict(d)
        assert r2.title == r.title
        assert r2.date == r.date
        assert r2.participants == r.participants
        assert r2.cleaned_notes == r.cleaned_notes
        assert r2.summary == r.summary
        assert len(r2.decisions) == 1
        assert r2.decisions[0].topic == "Tech stack"
        assert len(r2.action_items) == 1
        assert r2.action_items[0].owner == "Alice"

    def test_to_json(self):
        r = MeetingRecord(title="Test", date="2026-01-01")
        j = r.to_json()
        assert '"title": "Test"' in j
        assert '"date": "2026-01-01"' in j


class TestDecision:
    def test_create(self):
        d = Decision(topic="Database", outcome="Use SQLite", rationale="Simple and portable")
        assert d.topic == "Database"
        assert d.outcome == "Use SQLite"

    def test_roundtrip(self):
        d = Decision(topic="A", outcome="B", rationale="C")
        d2 = Decision.from_dict(d.to_dict())
        assert d2.topic == "A"
        assert d2.outcome == "B"
        assert d2.rationale == "C"


class TestActionItem:
    def test_create(self):
        a = ActionItem(owner="Bob", description="Fix bug", deadline="2026-11-15")
        assert a.owner == "Bob"
        assert a.description == "Fix bug"
        assert a.deadline == "2026-11-15"
        assert a.status == "open"

    def test_roundtrip(self):
        a = ActionItem(owner="Alice", description="Deploy", deadline=None)
        a2 = ActionItem.from_dict(a.to_dict())
        assert a2.owner == "Alice"
        assert a2.description == "Deploy"
        assert a2.deadline is None