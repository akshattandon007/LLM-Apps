"""
PlainTranslator Agent — Rewrites legal clauses in plain, accessible language.
"""

import json
import re
from typing import Optional


CONFIDENCE_KEYWORDS = {
    "low": ["maybe", "might", "could", "possibly", "if applicable", "subject to"],
    "medium": ["typically", "generally", "usually", "often", "in most cases"],
    "high": ["must", "will", "shall", "guaranteed", "required", "mandatory"],
}


def _rule_based_translate(clause: dict) -> dict:
    """
    Simple rule-based plain-language translation for fallback.
    """
    text = clause.get("text", "")
    replacements = [
        (r"(?i)\bherein\b", "in this document"),
        (r"(?i)\bhereinafter\b", "from now on"),
        (r"(?i)\bwhereas\b", "while"),
        (r"(?i)\bnotwithstanding\b", "even if"),
        (r"(?i)\bhereto\b", "to this agreement"),
        (r"(?i)\bhereof\b", "of this agreement"),
        (r"(?i)\bpursuant to\b", "according to"),
        (r"(?i)\bindemnify\b", "protect from loss"),
        (r"(?i)\barbitration\b", "a private legal process outside court"),
        (r"(?i)\bforce majeure\b", "unavoidable events outside our control"),
        (r"(?i)\bbinding\b", "legally required"),
        (r"(?i)\bwithout prejudice\b", "without giving up legal rights"),
        (r"(?i)\bprorogation\b", "postponement"),
    ]

    plain_text = text
    for pattern, replacement in replacements:
        plain_text = re.sub(pattern, replacement, plain_text)

    # Simplify sentence structure
    plain_text = re.sub(r'\,(?=\s*(?:and|or|but|however|provided))', '', plain_text)
    plain_text = re.sub(r'said\s+(agreement|party|document|clause)', r'the \1', plain_text, flags=re.I)

    return {
        "plain_text": plain_text[:1500],
        "confidence": 0.5,
        "method": "rule_based",
    }


class PlainTranslator:
    """
    Agent 2: Translates legal/contract language into plain English
    at approximately a 6th-grade reading level.
    """

    def __init__(self, api_key: str = "", model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self._llm_available = bool(api_key)

    def translate(self, clauses: list[dict]) -> list[dict]:
        """
        Translate each clause into plain language.

        Args:
            clauses: List of clause dicts from ClauseExtractor

        Returns:
            List of translation dicts with keys: plain_text, confidence
        """
        results = []
        for clause in clauses:
            result = self._translate_single(clause)
            results.append(result)
        return results

    def _translate_single(self, clause: dict) -> dict:
        """Translate a single clause."""
        if not self._llm_available:
            return _rule_based_translate(clause)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            text = clause.get("text", "")[:2000]

            prompt = f"""Rewrite the following legal clause in SIMPLE, PLAIN LANGUAGE that someone with a 6th-grade education can understand.

Rules:
- Use short sentences (under 20 words)
- Replace every legal term with everyday language
- Keep all legal obligations and commitments intact — do not soften them
- Do NOT add opinions or warnings (that's another agent's job)
- State what the clause ACTUALLY means for both parties
- Be direct: "You must..." / "The company must..." / "You agree that..."

Also return a confidence score (0.0 to 1.0) for how well you understood the clause.

Respond in this EXACT JSON format:
{{
  "plain_text": "your plain language version here",
  "confidence": 0.95
}}

CLAUSE TYPE: {clause.get('type', 'unknown')}
ORIGINAL TEXT:
{text}
"""

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You translate legal language to plain English. Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1000,
            )

            raw = response.choices[0].message.content.strip()
            raw = re.sub(r'^```(?:json)?\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)

            result = json.loads(raw)
            return {
                "plain_text": result.get("plain_text", text)[:1500],
                "confidence": min(max(float(result.get("confidence", 0.5)), 0.0), 1.0),
                "method": "llm",
            }

        except Exception as e:
            print(f"  ⚠️ LLM translation failed ({e}), falling back to rule-based...")
            return _rule_based_translate(clause)
