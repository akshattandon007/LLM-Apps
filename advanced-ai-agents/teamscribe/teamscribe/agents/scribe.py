"""Agent 3 — Scribe: generates meeting summary and follow-up email."""

from teamscribe.agent_base import BaseAgent
from teamscribe.models import MeetingRecord


class Scribe(BaseAgent):
    """Drafts a concise meeting summary and follow-up email."""

    def __init__(self, **kwargs):
        super().__init__(
            name="Scribe",
            role="a professional meeting summarizer who writes clear, actionable summaries and polished follow-up emails",
            **kwargs,
        )

    def process(self, record: MeetingRecord) -> MeetingRecord:
        """Generate summary and follow-up email from cleaned notes + decisions."""
        record.summary = self._generate_summary(record)
        record.follow_up_email = self._generate_email(record)
        return record

    def _generate_summary(self, record: MeetingRecord) -> str:
        system = (
            "Write a concise meeting summary (2-4 paragraphs). Include:\n"
            "- What was discussed (top level)\n"
            "- Key decisions reached\n"
            "- Action items with owners\n"
            "- Any blockers or risks mentioned\n\n"
            "Use professional but plain language. No markdown formatting."
        )
        return self.call_llm(system, self._build_context(record))

    def _generate_email(self, record: MeetingRecord) -> str:
        system = (
            "Write a professional follow-up email summarizing the meeting. "
            "Format it as a plain-text email with:\n"
            "- A subject line (first line starting with 'Subject:')\n"
            "- A brief greeting\n"
            "- Bullet summary of what was discussed\n"
            "- Action items with owners\n"
            "- Next steps and deadlines\n"
            "- A polite closing\n\n"
            "Keep it under 300 words. No markdown."
        )
        return self.call_llm(system, self._build_context(record))

    def _build_context(self, record: MeetingRecord) -> str:
        ctx = (
            f"Title: {record.title}\n"
            f"Date: {record.date}\n"
            f"Participants: {', '.join(record.participants)}\n\n"
            f"Cleaned Notes:\n{record.cleaned_notes}\n\n"
        )
        if record.decisions:
            ctx += "Decisions:\n" + "\n".join(
                f"- {d.topic}: {d.outcome}" for d in record.decisions
            ) + "\n\n"
        if record.action_items:
            ctx += "Action Items:\n" + "\n".join(
                f"- {a.owner}: {a.description}" + (f" (by {a.deadline})" if a.deadline else "")
                for a in record.action_items
            ) + "\n"
        return ctx