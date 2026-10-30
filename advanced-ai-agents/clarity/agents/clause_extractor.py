"""
ClauseExtractor Agent — Identifies obligations, deadlines, fees, and penalties
from legal document text using LLM-based extraction.
"""

import json
import re
from typing import Optional


CLAUSE_TYPES = [
    "payment_and_fees",
    "termination_and_cancellation",
    "renewal_and_auto_renewal",
    "liability_and_indemnification",
    "dispute_resolution_and_arbitration",
    "confidentiality_and_privacy",
    "intellectual_property",
    "warranty_and_disclaimer",
    "amendment_and_modification",
    "governing_law_and_jurisdiction",
    "non_compete_and_restrictive_covenant",
    "force_majeure",
    "assignment_and_transfer",
    "notice_and_communication",
    "definitions_and_interpretation",
    "general_provisions",
]


# Rule-based fallback patterns for when LLM is unavailable
PATTERNS = {
    "payment_and_fees": [
        r"(?i)(?:shall\s+)?(?:pay|fee|charge|cost|price|rate|deposit|penalty|late\s+fee)",
        r"(?i)(?:interest|annual|monthly|installment|due\s+on|billing)"
    ],
    "termination_and_cancellation": [
        r"(?i)(?:terminate|cancel|end\s+(?:this\s+)?agreement|dissolve|rescind)",
        r"(?i)(?:termination\s+(?:fee|cost|penalty|notice|date))"
    ],
    "renewal_and_auto_renewal": [
        r"(?i)(?:renew|auto.?renew|extend|rollover|perpetual)",
        r"(?i)(?:renewal\s+(?:term|period|notice|fee))"
    ],
    "liability_and_indemnification": [
        r"(?i)(?:indemnif|hold\s+harmless|liable|liability|damages|waive)",
        r"(?i)(?:limitation\s+of\s+liability|maximum\s+liability|cap\s+on\s+liability)"
    ],
    "dispute_resolution_and_arbitration": [
        r"(?i)(?:arbitrat|arbitration|mediation|dispute|litigation|class\s+action)",
        r"(?i)(?:binding\s+arbitration|waive\s+right\s+to\s+sue|jury\s+trial)"
    ],
    "confidentiality_and_privacy": [
        r"(?i)(?:confidential|privacy|data\s+(?:protection|sharing|collection)|NDA)",
        r"(?i)(?:non.?disclosure|trade\s+secret|personal\s+information)"
    ],
    "intellectual_property": [
        r"(?i)(?:intellectual\s+property|copyright|trademark|patent|license)",
        r"(?i)(?:IP\s+(?:rights|ownership)|work\s+(?:made\s+for\s+hire|product))"
    ],
}


def _rule_based_extract(text: str) -> list[dict]:
    """Fallback extraction using regex patterns when LLM is unavailable."""
    clauses = []
    paragraphs = re.split(r'\n\s*\n', text)
    for para in paragraphs:
        para = para.strip()
        if len(para) < 20:
            continue
        matched_types = []
        for ctype, patterns in PATTERNS.items():
            for pat in patterns:
                if re.search(pat, para):
                    matched_types.append(ctype)
                    break
        if matched_types:
            clauses.append({
                "text": para[:1500],
                "type": matched_types[0],
                "all_types": matched_types,
                "source": "rule_based",
            })
    return clauses


class ClauseExtractor:
    """
    Agent 1: Extracts structured clauses from legal document text.
    Identifies obligations, deadlines, fees, penalties, auto-renewal, etc.
    """

    def __init__(self, api_key: str = "", model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self._llm_available = bool(api_key)

    def extract(self, document: str) -> list[dict]:
        """
        Extract clauses from the document.

        Args:
            document: Full document text

        Returns:
            List of clause dicts with keys: text, type, all_types
        """
        if not document.strip():
            return []

        if self._llm_available:
            return self._llm_extract(document)
        else:
            return _rule_based_extract(document)

    def _llm_extract(self, document: str) -> list[dict]:
        """
        Use LLM to intelligently extract and classify clauses.
        Falls back to rule-based if API call fails.
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            clause_types_str = "\n".join(f"- {ct}" for ct in CLAUSE_TYPES)

            prompt = f"""You are a legal contract clause extractor. Given a document, identify every distinct clause or provision.

Return a JSON array of objects. Each object has:
  "text": the exact clause text (preserve original wording),
  "type": the most specific clause type from the list below,
  "all_types": array of all matching types from the list below.

Clause types:
{clause_types_str}

Rules:
- Each clause must be a distinct, self-contained provision
- Include obligations, deadlines, fees, penalties, rights, and restrictions
- If a paragraph contains multiple provisions, split them
- Return ONLY valid JSON array — no markdown, no backticks, no explanation
- If the text is not a legal document, return an empty array []

DOCUMENT TEXT:
{document[:8000]}
"""

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You extract legal clauses from documents. Return only valid JSON arrays."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=4000,
            )

            raw = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            raw = re.sub(r'^```(?:json)?\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)

            clauses = json.loads(raw)
            if not isinstance(clauses, list):
                raise ValueError("Response was not a list")
            return clauses

        except Exception as e:
            print(f"  ⚠️ LLM extraction failed ({e}), falling back to rule-based...")
            return _rule_based_extract(document)
