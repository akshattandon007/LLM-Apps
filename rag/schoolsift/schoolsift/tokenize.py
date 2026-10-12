"""Tokenization and feature extraction for Schoolsift's retrieval core."""
from __future__ import annotations

import re

# Small English stopword list — enough to keep school questions meaningful
# ("when", "is", "the" carry no signal) without dragging in a full NLP dep.
STOPWORDS = frozenset(
    """
    a an and are as at be by for from has he her his how i in is it its of on
    or she that the their they this to was we were will with you your do does
    did done can could should would what when where which who whom whose why
    not no don t s ve re ll
    """.split()
)

_WORD_RE = re.compile(r"[a-z0-9][a-z0-9'’]*", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric tokens, dropping stopwords and 1-char tokens."""
    out = []
    for m in _WORD_RE.finditer(text.lower()):
        tok = m.group(0)
        if tok in STOPWORDS or len(tok) < 2:
            continue
        out.append(tok)
    return out


def terms(text: str) -> list[str]:
    """Feature terms for a text: unigrams plus significant bigrams.

    School documents are phrase-dense ("science fair", "permission slip",
    "book fair") — the bigram features make phrase-level retrieval work
    without an embedding model.
    """
    toks = tokenize(text)
    feats = list(toks)
    for a, b in zip(toks, toks[1:]):
        if len(a) >= 3 and len(b) >= 3:
            feats.append(f"{a}_{b}")
    return feats