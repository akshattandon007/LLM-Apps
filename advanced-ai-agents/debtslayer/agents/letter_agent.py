"""Agent: Letter Agent — drafts creditor negotiation letters.

Uses template-based drafting (zero API dependencies).
Can be upgraded to use any LLM provider by setting the DEEPSEEK_API_KEY
or OPENAI_API_KEY environment variable.
"""
from __future__ import annotations
import os
import json
from typing import Optional
from ..models import CreditorLetter


class LetterAgent:
    """Drafts personalized negotiation letters for creditors."""

    def __init__(self, llm_api_key: Optional[str] = None):
        self.api_key = llm_api_key or os.environ.get("LLM_API_KEY", "")

    def _template_letter(self, creditor: str, balance: float, apr: float, hardship: str) -> str:
        """Generate a letter from a professional template."""
        templates = {
            "reduced hours": (
                f"I am writing to discuss my {creditor} account (balance: ${balance:.2f}, "
                f"APR: {apr:.2f}%). Due to a recent reduction in my work hours, my income "
                f"has decreased substantially. I remain committed to fulfilling my obligation "
                f"but am unable to maintain the current payment schedule at the existing interest rate.\n\n"
                f"I am requesting a temporary reduction in my APR to help me avoid default "
                f"while I stabilize my income. A reduction to [X]% would allow me to continue "
                f"making consistent payments and eventually pay off the full balance. I am prepared "
                f"to provide documentation of my reduced hours upon request."
            ),
            "medical": (
                f"I am writing concerning my {creditor} account (balance: ${balance:.2f}, "
                f"APR: {apr:.2f}%). Recently, I have incurred unexpected medical expenses "
                f"that have strained my finances. Despite this setback, I am determined to "
                f"honor my debt obligation.\n\n"
                f"I am requesting a hardship accommodation: either a temporary APR reduction "
                f"or a revised payment plan that reflects my current financial situation. "
                f"I am able to commit to consistent, reduced payments and will resume full "
                f"payments once my medical situation stabilizes."
            ),
            "job loss": (
                f"I am writing to request assistance with my {creditor} account "
                f"(balance: ${balance:.2f}, APR: {apr:.2f}%). I recently lost my job "
                f"and my primary source of income has been interrupted.\n\n"
                f"I am actively seeking new employment and intend to resume payments as soon "
                f"as I secure a new position. In the interim, I am requesting a temporary "
                f"hardship program — either a reduced payment plan, interest waiver, or "
                f"payment deferral. Please let me know what hardship options are available "
                f"for customers in my situation."
            ),
            "general": (
                f"I am writing regarding my {creditor} account (balance: ${balance:.2f}, "
                f"APR: {apr:.2f}%). Due to unforeseen financial circumstances "
                f"({hardship}), I am experiencing temporary difficulty maintaining my "
                f"current payment schedule.\n\n"
                f"I am committed to paying off this debt in full. I am requesting a "
                f"temporary APR reduction or hardship payment plan that would allow me "
                f"to continue making consistent payments while I work through this period. "
                f"I would appreciate learning what options are available."
            ),
        }

        # Find the best-matching template
        hl = hardship.lower()
        if any(w in hl for w in ["hour", "reduced", "cut", "part-time", "schedule"]):
            body = templates["reduced hours"]
        elif any(w in hl for w in ["medical", "health", "surgery", "hospital", "illness"]):
            body = templates["medical"]
        elif any(w in hl for w in ["job", "employ", "laid", "fired", "terminated"]):
            body = templates["job loss"]
        else:
            body = templates["general"]

        return body

    def draft_letter(
        self,
        creditor: str,
        balance: float,
        apr: float,
        hardship_reason: str = "unexpected financial difficulties",
    ) -> CreditorLetter:
        """Draft a creditor negotiation letter.
        
        Uses an LLM if API key is configured, otherwise falls back to templates.
        """
        use_llm = bool(self.api_key)

        if use_llm:
            body = self._llm_draft(creditor, balance, apr, hardship_reason)
        else:
            body = self._template_letter(creditor, balance, apr, hardship_reason)

        return CreditorLetter(
            creditor_name=creditor,
            balance=balance,
            apr=apr,
            hardship_reason=hardship_reason,
            body=body,
        )

    def _llm_draft(self, creditor: str, balance: float, apr: float, hardship: str) -> str:
        """Use an LLM API to draft a personalized letter. (Stub — requires API setup.)"""
        # In a real deployment, call OpenAI/Debugger API here.
        # For now, fall back to template.
        return self._template_letter(creditor, balance, apr, hardship)