"""Agent 1 — Transcriber: cleans up raw meeting notes."""

from teamscribe.agent_base import BaseAgent
from teamscribe.models import MeetingRecord


class Transcriber(BaseAgent):
    """Cleans up raw, messy meeting notes into coherent, structured text."""

    def __init__(self, **kwargs):
        super().__init__(
            name="Transcriber",
            role="a careful editor who cleans up raw meeting notes — fixing typos, removing filler, organizing chronological flow, and preserving every substantive point",
            **kwargs,
        )

    def process(self, record: MeetingRecord) -> MeetingRecord:
        """Take raw notes and return cleaned version."""
        system = (
            "You are a meticulous meeting-note editor. Your job is to:\n"
            "1. Fix typos, grammar, and awkward phrasing\n"
            "2. Remove filler words and off-topic tangents\n"
            "3. Organize notes in chronological order if they are jumbled\n"
            "4. Preserve EVERY substantive point — never delete important content\n"
            "5. Use bullet points for clarity where appropriate\n"
            "6. Never add information that wasn't in the original notes\n\n"
            "Output ONLY the cleaned notes, no commentary."
        )
        user = f"Meeting: {record.title}\nDate: {record.date}\nParticipants: {', '.join(record.participants)}\n\nRaw notes:\n{record.raw_notes}"
        record.cleaned_notes = self.call_llm(system, user)
        return record