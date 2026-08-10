"""Query intent classification — keyword + semantic scoring."""
from __future__ import annotations

import re

from src.models import Intent

# ----- Keyword-based intent rules -----

_INTENT_RULES: list[tuple[re.Pattern, Intent]] = [
    # Vaccination checks first because "tetanus shot" is specific
    (re.compile(r"(?i)\b(vaccination|vaccine|shot|immunization|booster|tetanus|flu\s*shot|covid\s*vaccine|hpv|tdap|dose\s*of)\b"), Intent.VACCINATION),
    # Temporal trend — "change over", "how has ... changed", "between ... and", "compared to", "trend"
    (re.compile(r"(?i)\b(change|trend|over\s+time|between\s+\w+\s+and\s+\w+|compared\s+to|how\s+(?:has|did|have)\s+.*\s+change)\b"), Intent.TEMPORAL_TREND),
    # Medication history
    (re.compile(r"(?i)\b(medications?|prescription|taking|dose|dosage|what\s*(?:was|were|am)\s*I\s*on)\b"), Intent.MEDICATION_HISTORY),
    # Lab value query
    (re.compile(r"(?i)\b(hba1c|a1c|ldl|hdl|cholesterol|vitamin|glucose|lipid|lab|result|level|count|value|what\s*(?:was|is|were|are)\s*my)\b"), Intent.LAB_VALUE),
]

# Temporal keywords that can override to TEMPORAL_TREND
_TEMPORAL_OVERRIDE = re.compile(r"(?i)(change|trend|over\s+(the\s+)?(past|last|time)|between\s+.*\s+and\s+.*\s+\d{4})")


def classify_intent(question: str) -> Intent:
    """Classify a user question into one of the 5 intent categories.

    Uses keyword-based scoring with temporal override logic.
    """
    # Check for temporal trend override first (e.g., "How did my LDL change between X and Y")
    if _TEMPORAL_OVERRIDE.search(question):
        # But only if it's not clearly a pure vaccination query
        if not re.search(r"(?i)\b(vaccination|vaccine|shot|immunization|tetanus|booster)\b", question):
            return Intent.TEMPORAL_TREND

    scores: dict[Intent, int] = {intent: 0 for intent in Intent}

    for pattern, intent in _INTENT_RULES:
        matches = pattern.findall(question)
        scores[intent] += len(matches)

    # If nothing matched, return GENERAL_INFO
    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    if scores[best] == 0:
        return Intent.GENERAL_INFO

    # If temporal trend has any score and question mentions a time range, prefer it
    if scores[Intent.TEMPORAL_TREND] > 0 and _TEMPORAL_OVERRIDE.search(question):
        return Intent.TEMPORAL_TREND

    return best  # type: ignore[return-value]