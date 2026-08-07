"""Query-to-legal-domain classifier.

Given a natural-language question about a lease, predicts which legal domain
is most relevant (RENT, TERMINATION, ACCESS, MAINTENANCE, PETS, SUBLETTING,
DEPOSIT, UTILITIES, or GENERAL). Uses keyword heuristics rather than an LLM
call — faster, cheaper, and sufficient for domain routing.
"""

import re
from typing import Optional

from src.models import LEGAL_DOMAINS


# Domain-specific keyword patterns — ordered by specificity.
_DOMAIN_PATTERNS: list[tuple[str, re.Pattern]] = [
    # RENT
    ("RENT", re.compile(
        r"(rent|late\s*fee|grace\s*period|due\s*date|monthly\s*payment|"
        r"rent\s*increase|how\s+much\s+do\s+i\s+pay|when\s+is\s+rent\s+due)", re.I
    )),
    # TERMINATION
    ("TERMINATION", re.compile(
        r"(break\s+(the\s+)?lease|early\s+termination|notice\s+to\s+vacate|"
        r"leave\s+early|move\s+out\s+early|end\s+(the\s+)?lease|terminat|"
        r"cancel\s+lease|abandon)", re.I
    )),
    # ACCESS
    ("ACCESS", re.compile(
        r"(landlord\s+enter|enter\s+without\s+notice|right\s+of\s+entry|"
        r"access\s+unit|notice\s+before\s+entering|show\s+(the\s+)?unit|"
        r"inspect\s+apartment|landlord\s+access)", re.I
    )),
    # MAINTENANCE
    ("MAINTENANCE", re.compile(
        r"(maintenance|repair|fix|broken|damage|habitable|working\s+order|"
        r"landlord\s+fix|who\s+fixes|pest\s+control|mold|plumbing|"
        r"electrical|heating|air\s+conditioning)", re.I
    )),
    # PETS
    ("PETS", re.compile(
        r"(pet|dog|cat|animal|esa|emotional\s+support|service\s+animal|"
        r"pet\s+deposit|pet\s+rent|pet\s+policy)", re.I
    )),
    # SUBLETTING
    ("SUBLETTING", re.compile(
        r"(sublet|sublease|assign|roommate|take\s+over\s+lease|"
        r"transfer\s+lease|someone\s+else\s+live)", re.I
    )),
    # DEPOSIT
    ("DEPOSIT", re.compile(
        r"(security\s*deposit|deposit\s+refund|get\s+deposit\s*back|"
        r"damage\s+deduction|deposit\s+return|how\s+much\s+deposit)", re.I
    )),
    # UTILITIES
    ("UTILITIES", re.compile(
        r"(utilit|electric|water|gas|internet|trash|sewer|who\s+pays\s+for)", re.I
    )),
]


def classify_query(question: str) -> str:
    """Predict the legal domain for a user question.

    Iterates patterns in order; returns the first match. Falls back to GENERAL.
    """
    for domain, pattern in _DOMAIN_PATTERNS:
        if pattern.search(question):
            return domain
    return "GENERAL"


def classify_query_with_confidence(question: str) -> tuple[str, float]:
    """Predict domain and return a confidence score.

    Confidence is a rough heuristic based on match quality:
    - 0.9+ if the domain keyword is a primary subject
    - 0.7 if matched via secondary keywords
    - 0.3 on GENERAL fallback
    """
    # Primary subject patterns (higher confidence)
    primary_patterns = {
        "RENT": re.compile(
            r"^(how\s+much|when\s+is|what\s+is\s+the\s+rent|can\s+they\s+raise)", re.I
        ),
        "TERMINATION": re.compile(
            r"^(what\s+happens\s+if|can\s+i\s+(break|leave|terminate)|"
            r"how\s+do\s+i\s+(break|leave|terminate))", re.I
        ),
        "ACCESS": re.compile(
            r"^(can\s+(my\s+)?landlord\s+(enter|come|access)|"
            r"does\s+(my\s+)?landlord\s+need)", re.I
        ),
        "DEPOSIT": re.compile(r"^(will\s+i\s+get|how\s+do\s+i\s+get|deposit)", re.I),
    }

    domain = classify_query(question)
    if domain == "GENERAL":
        return domain, 0.3

    primary = primary_patterns.get(domain)
    if primary and primary.search(question):
        return domain, 0.9
    return domain, 0.7