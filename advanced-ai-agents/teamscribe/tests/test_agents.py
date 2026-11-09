"""Tests for TeamScribe agents (mocked LLM)."""

from unittest.mock import patch, MagicMock

from teamscribe.models import MeetingRecord
from teamscribe.agents.transcriber import Transcriber
from teamscribe.agents.minute_taker import MinuteTaker
from teamscribe.agents.scribe import Scribe
from teamscribe.agents.archivist import Archivist


SAMPLE_RAW = """Alice: Let's discuss the new feature
Bob: I think we should use Python for the backend
Alice: Agreed. Also need to update the docs
Bob: I can handle that by Friday
Decision: We'll go with Python + FastAPI
Action: Bob to update documentation by Friday"""

SAMPLE_CLEANED = """- Discussed new feature implementation
- Agreed on Python + FastAPI for backend
- Bob will update documentation by Friday
- Decision made: Python + FastAPI"""


def make_record() -> MeetingRecord:
    return MeetingRecord(
        title="Sprint Planning",
        date="2026-11-09",
        participants=["Alice", "Bob"],
        raw_notes=SAMPLE_RAW,
    )


class TestTranscriber:
    def test_process_calls_llm(self):
        agent = Transcriber(model="gpt-4o-mini")
        agent.call_llm = MagicMock(return_value=SAMPLE_CLEANED)
        record = agent.process(make_record())
        assert record.cleaned_notes == SAMPLE_CLEANED
        agent.call_llm.assert_called_once()


class TestMinuteTaker:
    def test_process_parses_json(self):
        agent = MinuteTaker(model="gpt-4o-mini")
        agent.call_llm = MagicMock(return_value='''{
            "decisions": [{"topic": "Tech stack", "outcome": "Python + FastAPI", "rationale": "Team preference"}],
            "action_items": [{"owner": "Bob", "description": "Update documentation", "deadline": "2026-11-12"}],
            "key_points": ["Chose Python + FastAPI", "Documentation needs updating"]
        }''')
        record = agent.process(make_record())
        assert len(record.decisions) == 1
        assert record.decisions[0].topic == "Tech stack"
        assert len(record.action_items) == 1
        assert record.action_items[0].owner == "Bob"
        assert len(record.key_points) == 2

    def test_handles_malformed_json(self):
        agent = MinuteTaker(model="gpt-4o-mini")
        agent.call_llm = MagicMock(return_value="No JSON here, just text")
        record = agent.process(make_record())
        assert record.decisions == []
        assert record.action_items == []
        assert record.key_points == []


class TestScribe:
    def test_process_generates_summary_and_email(self):
        agent = Scribe(model="gpt-4o-mini")
        record = make_record()
        record.cleaned_notes = SAMPLE_CLEANED
        agent.call_llm = MagicMock(return_value="Meeting summary text")
        agent._generate_email = MagicMock(return_value="Subject: Follow-up\n\nThanks team,")
        record = agent.process(record)
        assert record.summary == "Meeting summary text"
        assert "Subject:" in record.follow_up_email


class TestArchivist:
    def test_archive_operations(self, tmp_path):
        archive_path = str(tmp_path / "archive.json")
        agent = Archivist(model="gpt-4o-mini", archive_path=archive_path)
        agent.call_llm = MagicMock(return_value="[]")

        record = make_record()
        record.cleaned_notes = SAMPLE_CLEANED
        record.decisions = []  # no decisions for first test

        result = agent.process(record)
        # Should have saved archive
        assert agent.archive_path.exists()
        import json
        data = json.loads(agent.archive_path.read_text())
        assert len(data["meetings"]) == 1
        assert data["meetings"][0]["title"] == "Sprint Planning"