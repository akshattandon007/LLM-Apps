"""Small shared text helpers: sentence splitting and whitespace cleanup."""
from __future__ import annotations

import re

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")


def split_sentences(text: str) -> list[str]:
    """Split text into sentences on punctuation or newlines.

    This is intentionally heuristic — school paperwork is full of 'Mrs.'
    abbreviations which a naive splitter will cut at, but for chunk quoting
    and date-context extraction the slight imperfection is acceptable.
    """
    return [p.strip() for p in _SENTENCE_SPLIT_RE.split(text) if p.strip()]


def clean_whitespace(text: str) -> str:
    """Collapse runs of whitespace to single spaces."""
    return " ".join(text.split())