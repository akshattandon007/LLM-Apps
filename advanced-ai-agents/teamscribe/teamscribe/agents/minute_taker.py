"""Agent 2 — MinuteTaker: extracts decisions and action items."""

from __future__ import annotations

import json
import re

from teamscribe.agent_base import BaseAgent
from teamscribe.models import MeetingRecord, Decision, ActionItem


class MinuteTaker(BaseAgent):
    """Extracts decisions, action items, and key points from cleaned notes."""

    def __init__(self, **kwargs):
        super().__init__(
            name="MinuteTaker",
            role="a sharp meeting analyst who extracts decisions, action items, and key discussion points from meeting notes",
            **kwargs,
        )

    def process(self, record: MeetingRecord) -> MeetingRecord:
        """Parse cleaned notes and populate decisions, action items, key points."""
        system = (
            "You extract structured information from meeting notes. "
            "Return ONLY a valid JSON object with these keys:\n"
            "- decisions: list of objects with keys 'topic', 'outcome', 'rationale'\n"
            "- action_items: list of objects with keys 'owner', 'description', 'deadline' (or null)\n"
            "- key_points: list of strings (max 8 most important discussion points)\n\n"
            "If a field is not found in the notes, use empty list or null.\n"
            "Do NOT add anything that isn't supported by the notes."
        )
        user = (
            f"Meeting: {record.title}\n"
            f"Date: {record.date}\n"
            f"Participants: {', '.join(record.participants)}\n\n"
            f"Cleaned notes:\n{record.cleaned_notes}"
        )
        raw = self.call_llm(system, user, temperature=0.1)

        # Parse JSON from response (handle code fences)
        json_str = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.DOTALL)
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            # Try to extract JSON block
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
            else:
                data = {"decisions": [], "action_items": [], "key_points": []}

        record.decisions = [
            Decision(topic=d.get("topic", ""), outcome=d.get("outcome", ""), rationale=d.get("rationale", ""))
            for d in data.get("decisions", [])
        ]
        record.action_items = [
            ActionItem(owner=a.get("owner", ""), description=a.get("description", ""), deadline=a.get("deadline"))
            for a in data.get("action_items", [])
        ]
        record.key_points = data.get("key_points", [])
        return record