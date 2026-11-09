"""Tests for TeamScribe orchestrator and storage."""

import json
from pathlib import Path
from unittest.mock import MagicMock

from teamscribe.models import MeetingRecord
from teamscribe.orchestrator import Orchestrator
from teamscribe.storage import Storage


SAMPLE_RAW = "Alice: Let's use Python\nBob: Sounds good"
SAMPLE_CLEANED = "- Agreed on Python"
FAKE_SUMMARY = "Team agreed on Python for the project."
FAKE_EMAIL = "Subject: Meeting follow-up\n\nThanks all,"


class TestOrchestrator:
    def test_run_pipeline(self):
        """All 4 agents run in sequence with mocked LLM calls."""
        orch = Orchestrator(model="gpt-4o-mini")
        for agent in orch.agents:
            agent.call_llm = MagicMock(return_value=SAMPLE_CLEANED)
        # MinuteTaker needs JSON
        orch.agents[1].call_llm = MagicMock(return_value='{"decisions": [], "action_items": [], "key_points": ["Point 1"]}')
        # Scribe needs separate mocks
        orch.agents[2].call_llm = MagicMock(return_value=FAKE_SUMMARY)
        orch.agents[2]._generate_email = MagicMock(return_value=FAKE_EMAIL)
        # Archivist
        orch.agents[3].call_llm = MagicMock(return_value="[]")

        record = MeetingRecord(
            title="Quick Sync",
            date="2026-11-09",
            participants=["Alice", "Bob"],
            raw_notes=SAMPLE_RAW,
        )

        result = orch.run(record)
        assert result.title == "Quick Sync"
        assert len(result.cleaned_notes) > 0
        assert len(result.key_points) == 1

    def test_run_on_empty_raw(self):
        """Pipeline handles edge case of no raw notes."""
        orch = Orchestrator(model="gpt-4o-mini")
        for agent in orch.agents:
            agent.call_llm = MagicMock(return_value="")
        orch.agents[1].call_llm = MagicMock(return_value='{"decisions": [], "action_items": [], "key_points": []}')
        orch.agents[2].call_llm = MagicMock(return_value="")
        orch.agents[2]._generate_email = MagicMock(return_value="")
        orch.agents[3].call_llm = MagicMock(return_value="[]")

        record = MeetingRecord(title="Empty", date="2026-11-09", raw_notes="")
        result = orch.run(record)
        assert result.title == "Empty"


class TestStorage:
    def test_save_and_list(self, tmp_path):
        storage = Storage(output_dir=str(tmp_path))
        record = MeetingRecord(title="Test Meeting", date="2026-11-09")
        path = storage.save(record)
        assert path.exists()

        meetings = storage.list_meetings()
        assert len(meetings) == 1
        assert meetings[0]["title"] == "Test Meeting"

    def test_load_roundtrip(self, tmp_path):
        storage = Storage(output_dir=str(tmp_path))
        record = MeetingRecord(
            title="Roundtrip Test",
            date="2026-11-08",
            participants=["Alice"],
            raw_notes="hello",
        )
        path = storage.save(record)
        loaded = storage.load(path)
        assert loaded is not None
        assert loaded.title == "Roundtrip Test"
        assert loaded.raw_notes == "hello"
        assert loaded.participants == ["Alice"]

    def test_list_empty(self, tmp_path):
        storage = Storage(output_dir=str(tmp_path))
        assert storage.list_meetings() == []