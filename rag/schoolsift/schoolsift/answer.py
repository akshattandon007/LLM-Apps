"""Answer builder: turn retrieval hits into a cited, extractive answer.

This is retrieval-augmented generation without an LLM — the answer is the
best-matching sentence from the retrieved passages, always shown with the
source document and page, plus any dates/deadlines found. Deterministic,
offline, and impossible to hallucinate.
"""
from __future__ import annotations

from datetime import date

from .dates import extract_dates
from .textutil import clean_whitespace, split_sentences
from .tokenize import terms


def _cite(hit: dict) -> str:
    return f"{hit['doc']['title']} (p.{hit['chunk']['page']})"


def _snippet(text: str, limit: int = 220) -> str:
    clean = clean_whitespace(text)
    return clean if len(clean) <= limit else clean[: limit - 1].rstrip() + "…"


def _best_sentence(text: str, qterms: set[str], min_len: int = 25) -> str:
    """Pick the sentence from a chunk that overlaps the question most.

    Ties (common with short queries) are broken by preferring a sentence
    that actually carries a calendar date, then by shortness — so a merged
    title fragment ("Science Fair Permission Slip ...") loses to the crisp
    date sentence underneath it.
    """
    candidates: list[str] = []
    best_overlap = 0
    for sentence in split_sentences(text):
        if len(sentence) < min_len:
            continue
        overlap = len(set(terms(sentence)) & qterms)
        if overlap > best_overlap:
            best_overlap = overlap
            candidates = [sentence]
        elif overlap == best_overlap and overlap > 0:
            candidates.append(sentence)
    if not candidates:
        # Fallback: first reasonably sized sentence, or a snippet.
        for sentence in split_sentences(text):
            if len(sentence) >= 12:
                return clean_whitespace(sentence)
        return _snippet(text, 200)

    def tie_key(sentence: str) -> tuple[int, int]:
        has_date = 0 if extract_dates(sentence) else 1
        return (has_date, len(sentence))

    return clean_whitespace(min(candidates, key=tie_key))


def build_answer(store, question: str, hits: list[dict],
                 today: date | None = None, max_quotes: int = 3) -> str:
    """Compose the final answer text shown to the user."""
    lines = [f"Q: {question}"]
    if not hits:
        lines.append("I couldn't find anything relevant in the indexed documents.")
        lines.append("Try rephrasing, or index more files with:")
        lines.append("  python3 -m schoolsift index <folder>")
        return "\n".join(lines)

    qterms = set(terms(question))
    top = hits[0]
    answer_sentence = _best_sentence(top["chunk"]["text"], qterms)
    lines.append(f"A: {answer_sentence}")
    lines.append(f"   — {_cite(top)}")
    lines.append("")

    lines.append("Supporting passages:")
    for h in hits[:max_quotes]:
        lines.append(f"- {_cite(h)}: \"{_snippet(h['chunk']['text'])}\"")

    dates = extract_dates(
        " ".join(h["chunk"]["text"] for h in hits), today=today
    )
    if dates:
        lines.append("")
        lines.append("Key dates found in those passages:")
        seen: set[str] = set()
        for d in dates:
            if d.iso in seen:
                continue
            seen.add(d.iso)
            tag = " (deadline)" if d.kind == "deadline" else ""
            lines.append(f"- {d.iso}{tag} — {d.context[:140]}")
    return "\n".join(lines)