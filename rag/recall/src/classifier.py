"""Query intent classifier.

Classifies a user question into one of:
  - DECISION: explicit decisions made in the meeting
  - ACTION_ITEM: tasks, to-dos, follow-ups assigned
  - OPINION: someone's viewpoint, disagreement, agreement
  - FACT: factual statements, reports, updates
  - FOLLOW_UP: questions about next steps, future plans
"""

from __future__ import annotations

import re
from typing import Optional

# ── Lightweight keyword + pattern classifier ───────────────────────────────
# No LLM call needed for classification — this is fast, deterministic, and
# gets the job done for v1. Intent classification is a well-known problem
# where simple keyword/pattern methods work nearly as well as neural ones
# when the domain is narrow (meeting transcripts).


# Decision keywords
_DECISION_PATTERNS = [
    r"\bdecid(?:e|ed|es|ing)\b",
    r"\bdecision\b",
    r"\bagreed?\b",
    r"\bconsensus\b",
    r"\bresolved?\b",
    r"\bsettled?\b",
    r"\bfinal(?:ly|ized?| ize)\b",
    r"\bconcluded?\b",
    r"\bchosen?\b",
    r"\bgo with\b",
    r"\bwe['']?ll go\b",
    r"\bapproved?\b",
    r"\bsigned off\b",
    r"\blocked? in\b",
]

# Action item keywords
_ACTION_ITEM_PATTERNS = [
    r"\baction\s*items?\b",
    r"\btodo\b",
    r"\bto[- ]?do\b",
    r"\bfollow[- ]?up\b",
    r"\bwho (?:will|is|should)\b",
    r"\bassign(?:ed|s|ing)?\b",
    r"\bneed(?:s|ed)? to (?:do|send|create|update|check|prepare|write)\b",
    r"\bnext steps?\b",
    r"\bdeadline\b",
    r"\bowe(?:s|d)?\b",
    r"\bresponsible\b",
    r"\b(?:sarah|mike|alex|priya|james|emma)\s+(?:will|is going to|needs to|should)\b",
    r"\btask\b",
    r"\bhomework\b",
    r"\byou['']?ll (?:send|do|check|share|look|follow)\b",
]

# Opinion keywords
_OPINION_PATTERNS = [
    r"\bthink(?:s|ing)?\b",
    r"\bbelieve(?:s|d)?\b",
    r"\bfeel(?:s|ing)?\b",
    r"\bopinion\b",
    r"\bview(?:s|point)?\b",
    r"\bdisagree(?:d|s)?\b",
    r"\bagree(?:d|s)?\b",
    r"\bperspective\b",
    r"\bstance\b",
    r"\bposition\b",
    r"\bpush(?:ed|ing|es)? back\b",
    r"\bargue(?:d|s)?\b",
    r"\bconcern(?:s|ed)?\b",
    r"\bworr(?:y|ied|ies)\b",
    r"\bhesitant?\b",
    r"\bskeptic(?:al|ism)?\b",
    r"\bdoes\w+ think\b",
    r"\bsuggest(?:ed|s|ing)?\b",
    r"\brecommend(?:ed|s|ing)?\b",
]

# Follow-up keywords
_FOLLOW_UP_PATTERNS = [
    r"\bnext steps?\b",
    r"\bfollow[- ]?up\b",
    r"\bwhat(?:'s| is) next\b",
    r"\bupcoming\b",
    r"\bfuture\b",
    r"\bplan(?:s|ned|ning)?\b",
    r"\bschedule(?:d)?\b",
    r"\bwhen (?:will|is|are|should)\b",
    r"\btimeline\b",
    r"\bmilestone\b",
    r"\bupcoming\b",
    r"\bnext meeting\b",
    r"\bnext week\b",
    r"\bnext month\b",
]

# Fact keywords (broad — anything reporting is a fact)
_FACT_PATTERNS = [
    r"\bwhat (?:did|was|were|is|are)\b",
    r"\bwhat happened\b",
    r"\bsummary\b",
    r"\brecap\b",
    r"\breport(?:ed|s|ing)?\b",
    r"\bupdate(?:d|s)?\b",
    r"\bstatus\b",
    r"\bresult(?:s)?\b",
    r"\boutcome(?:s)?\b",
    r"\bsay(?:s)?\b",
    r"\bsaid?\b",
    r"\bmention(?:ed|s)?\b",
    r"\bpresent(?:ed|s)?\b",
    r"\bshow(?:ed|s)?\b",
    r"\bwhat(?:'s| is) the\b",
    r"\bnumbers?\b",
    r"\bdata\b",
    r"\bmetrics\b",
    r"\bfigure(?:s)?\b",
    r"\brevenue\b",
    r"\bbudget\b",
    r"\bcost(?:s)?\b",
    r"\bprice(?:s|ing)?\b",
]


def _score_patterns(query: str, patterns: list[str]) -> int:
    """Count how many patterns match the query."""
    query_lower = query.lower()
    score = 0
    for pat in patterns:
        if re.search(pat, query_lower):
            score += 1
    return score


# ── Speaker-lookup detection ───────────────────────────────────────────────
# If the question explicitly names a speaker, we still classify intent but
# we flag it for the retrieval stage.

_SPEAKER_NAMES = {"sarah", "mike", "alex", "priya", "james", "emma", "john", "lisa"}


def detect_speaker_mention(query: str) -> Optional[str]:
    """Return a speaker name if mentioned in the query, else None."""
    query_lower = query.lower()
    for name in _SPEAKER_NAMES:
        if name in query_lower:
            return name.capitalize()
    return None


_INTENT_ORDER = ["DECISION", "ACTION_ITEM", "FOLLOW_UP", "OPINION", "FACT"]


def classify_intent(query: str) -> str:
    """Classify query intent using keyword scoring.

    Returns one of: DECISION, ACTION_ITEM, OPINION, FACT, FOLLOW_UP
    """
    scores = {
        "DECISION": _score_patterns(query, _DECISION_PATTERNS),
        "ACTION_ITEM": _score_patterns(query, _ACTION_ITEM_PATTERNS),
        "OPINION": _score_patterns(query, _OPINION_PATTERNS),
        "FOLLOW_UP": _score_patterns(query, _FOLLOW_UP_PATTERNS),
        "FACT": _score_patterns(query, _FACT_PATTERNS),
    }

    # Return the highest-scoring intent. Ties broken by the order above.
    best = max(scores, key=lambda k: (scores[k], -_INTENT_ORDER.index(k)))

    # If no intent matches, default to FACT (safest fallback)
    if scores[best] == 0:
        return "FACT"

    return best