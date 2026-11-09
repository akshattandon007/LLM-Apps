"""Orchestrator — coordinates the 4-agent pipeline.

Agents run sequentially, each agent receiving and enriching the
shared MeetingRecord. The output of one agent feeds the next.
"""

from __future__ import annotations

from teamscribe.models import MeetingRecord
from teamscribe.agents import Transcriber, MinuteTaker, Scribe, Archivist


class Orchestrator:
    """Runs the TeamScribe multi-agent pipeline on a meeting."""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        archive_path: str | None = None,
    ):
        shared_kwargs = dict(model=model, api_key=api_key, base_url=base_url)
        self.agents = [
            Transcriber(**shared_kwargs),
            MinuteTaker(**shared_kwargs),
            Scribe(**shared_kwargs),
            Archivist(archive_path=archive_path, **shared_kwargs),
        ]

    def run(self, record: MeetingRecord) -> MeetingRecord:
        """Execute the full pipeline: all agents process the record in order."""
        print(f"📋 TeamScribe processing: {record.title}")
        print(f"   Date: {record.date}  |  Participants: {len(record.participants)}")

        for i, agent in enumerate(self.agents, 1):
            print(f"   [{i}/{len(self.agents)}] {agent.name}...", end=" ", flush=True)
            record = agent.process(record)
            print("✓")

        print(f"   ✅ Complete — {len(record.decisions)} decisions, "
              f"{len(record.action_items)} action items, "
              f"{len(record.key_points)} key points")
        return record