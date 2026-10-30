"""
RiskAdvisor Agent — Flags unfair terms, auto-renewal traps, hidden fees,
and generates questions the user should ask before signing.
"""

import json
import re
from typing import Optional


# High-risk flag patterns used for rule-based fallback
RISK_PATTERNS = {
    "auto_renewal": [
        r"(?i)(?:auto.?renew|automatically\s+renew|renew\s+automatically)",
        r"(?i)(?:shall\s+continue\s+(?:in\s+)?effect|perpetual\s+(?:term|agreement))",
    ],
    "binding_arbitration": [
        r"(?i)(?:binding\s+arbitration|waive\s+(?:any\s+)?right\s+to\s+(?:a\s+)?(?:court|jury|class\s+action))",
        r"(?i)(?:mandatory\s+arbitration|arbitration\s+(?:clause|provision|agreement))",
    ],
    "unilateral_amendment": [
        r"(?i)(?:may\s+(?:amend|change|modify|update)\s+(?:at\s+)?(?:any\s+)?time|sole\s+discretion)",
        r"(?i)(?:reserves?\s+the\s+right\s+to\s+(?:change|modify|amend)|without\s+(?:your\s+)?(?:consent|notice|approval))",
    ],
    "hidden_fee": [
        r"(?i)(?:administrative\s+fee|processing\s+fee|service\s+charge|convenience\s+fee)",
        r"(?i)(?:additional\s+(?:fees?|charges?|costs?)|not\s+included|may\s+apply)",
    ],
    "non_compete": [
        r"(?i)(?:non.?compete|non.?competition|restrictive\s+covenant)",
        r"(?i)(?:shall\s+not\s+(?:engage|compete|work\s+for)|prohibited\s+from\s+(?:working|engaging))",
    ],
    "liability_waiver": [
        r"(?i)(?:as.?is|without\s+(?:any\s+)?warranty|disclaim|waiv(?:e|er)\s+of\s+(?:all\s+)?liability)",
        r"(?i)(?:not\s+(?:liable|responsible)|limitation\s+of\s+liability|cap\s+on\s+(?:our\s+)?liability)",
    ],
    "early_termination_fee": [
        r"(?i)(?:early\s+termination\s+(?:fee|penalty|cost)|cancellation\s+(?:fee|penalty|charge))",
        r"(?i)(?:termination\s+(?:fee|cost|charge|penalty))",
    ],
    "automatic_data_sharing": [
        r"(?i)(?:share\s+(?:your\s+)?(?:data|information)\s+with\s+(?:third|affiliate))",
        r"(?i)(?:third.?party\s+(?:sharing|access|disclosure)|sell\s+(?:your\s+)?(?:data|information))",
    ],
    "indemnification": [
        r"(?i)(?:indemnif|hold\s+harmless|defend\s+(?:and\s+)?(?:indemnif|hold))",
        r"(?i)(?:shall\s+(?:indemnif|defend|hold\s+harmless))",
    ],
    "jurisdiction": [
        r"(?i)(?:governing\s+law|jurisdiction|venue\s+shall\s+be|exclusive\s+jurisdiction)",
        r"(?i)(?:disputes?\s+(?:shall\s+be\s+)?resolved\s+in|courts?\s+of)",
    ],
}


def _rule_based_risk(clause_text: str) -> tuple[list[str], float, str]:
    """Rule-based risk assessment when LLM is unavailable."""
    flags = []
    total_score = 0.0
    explanations = []

    for flag_name, patterns in RISK_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, clause_text):
                if flag_name not in flags:
                    flags.append(flag_name)
                    total_score += 0.3
                    explanations.append(f"Contains {flag_name.replace('_', ' ')} language")
                break

    score = min(total_score, 1.0)
    explanation = "; ".join(explanations) if explanations else "No specific high-risk patterns detected."
    return flags, score, explanation


class RiskAdvisor:
    """
    Agent 3: Assesses risk of each clause and flags problematic terms.
    Generates questions the user should ask before signing.
    """

    def __init__(self, api_key: str = "", model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self._llm_available = bool(api_key)

    def assess(self, clauses: list[dict], translations: list[dict], document: str) -> list[dict]:
        """
        Assess risk for each clause.

        Args:
            clauses: Extracted clauses from ClauseExtractor
            translations: Plain-language translations from PlainTranslator
            document: Original document text

        Returns:
            List of risk dicts with keys: score, flags, explanation
        """
        results = []
        for i, clause in enumerate(clauses):
            trans = translations[i] if i < len(translations) else {"plain_text": ""}
            result = self._assess_single(clause, trans)
            results.append(result)
        return results

    def _assess_single(self, clause: dict, translation: dict) -> dict:
        """Assess a single clause's risk level."""
        clause_text = clause.get("text", "")
        plain_text = translation.get("plain_text", "")

        if not self._llm_available:
            flags, score, explanation = _rule_based_risk(clause_text)
            return {"score": score, "flags": flags, "explanation": explanation}

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            text_for_analysis = f"Original: {clause_text[:1500]}\nPlain language: {plain_text[:800]}"

            prompt = f"""You are a consumer-protection legal advisor. Analyze this clause and assess its risk to the person SIGNING the document (NOT the drafter).

Return JSON with:
  "risk_score": float 0.0 (totally fair) to 1.0 (extremely risky),
  "flags": array of applicable flags from: auto_renewal, binding_arbitration, unilateral_amendment, hidden_fee, non_compete, liability_waiver, early_termination_fee, automatic_data_sharing, indemnification, jurisdiction,
  "explanation": 1-2 sentence plain-English explanation of why this is (or isn't) risky

Only flag genuine risks. If the clause is standard and fair, return score 0.1 and empty flags.

TEXT:
{text_for_analysis}

Respond ONLY valid JSON — no markdown, no backticks, no extra text.
"""

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You assess legal clause risk for consumers. Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=500,
            )

            raw = response.choices[0].message.content.strip()
            raw = re.sub(r'^```(?:json)?\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)

            result = json.loads(raw)
            return {
                "score": min(max(float(result.get("risk_score", 0)), 0.0), 1.0),
                "flags": result.get("flags", []),
                "explanation": result.get("explanation", ""),
            }

        except Exception as e:
            print(f"  ⚠️ LLM risk assessment failed ({e}), falling back to rule-based...")
            flags, score, explanation = _rule_based_risk(clause_text)
            return {"score": score, "flags": flags, "explanation": explanation}
