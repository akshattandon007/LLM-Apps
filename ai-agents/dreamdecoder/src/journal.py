"""Dream journal — persistent JSON-based storage for dream entries."""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Optional

from .models import DreamEntry, DreamStats, DreamInterpretation

JOURNAL_PATH = os.path.expanduser("~/.dreamdecoder_journal.json")


def _load_raw() -> dict:
    """Load the journal file as raw dict."""
    path = Path(JOURNAL_PATH)
    if not path.exists():
        return {"version": 1, "entries": []}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"version": 1, "entries": []}


def _save_raw(data: dict) -> None:
    """Atomically write the journal file."""
    path = Path(JOURNAL_PATH)
    tmp = path.with_suffix(".tmp")
    try:
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp.replace(path)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def save_entry(entry: DreamEntry) -> None:
    """Append a new entry to the journal."""
    data = _load_raw()
    entry.date = entry.date  # keep whatever was set
    data["entries"].append(entry.to_dict())
    _save_raw(data)


def load_all() -> list[DreamEntry]:
    """Return all entries, most recent first."""
    data = _load_raw()
    entries = [DreamEntry.from_dict(e) for e in data["entries"]]
    entries.sort(key=lambda e: e.date, reverse=True)
    return entries


def get_entry(entry_id: str) -> Optional[DreamEntry]:
    """Retrieve a single entry by ID."""
    for e in load_all():
        if e.id == entry_id:
            return e
    return None


def search_entries(query: str) -> list[DreamEntry]:
    """Search entries by keyword in dream text, symbols, or themes."""
    q = query.lower()
    results = []
    for entry in load_all():
        if q in entry.dream_text.lower():
            results.append(entry)
            continue
        if entry.interpretation:
            if q in entry.interpretation.interpretation.lower():
                results.append(entry)
                continue
            if any(q in s.lower() for s in entry.interpretation.symbols):
                results.append(entry)
                continue
            if any(q in t.lower() for t in entry.interpretation.themes):
                results.append(entry)
                continue
        if any(q in t.lower() for t in entry.tags):
            results.append(entry)
            continue
    return results


def delete_entry(entry_id: str) -> bool:
    """Delete an entry by ID. Returns True if found and deleted."""
    data = _load_raw()
    before = len(data["entries"])
    data["entries"] = [e for e in data["entries"] if e.get("id") != entry_id]
    if len(data["entries"]) == before:
        return False
    _save_raw(data)
    return True


def clear_all() -> int:
    """Clear all entries. Returns how many were removed."""
    data = _load_raw()
    count = len(data["entries"])
    data["entries"] = []
    _save_raw(data)
    return count


def compute_stats() -> DreamStats:
    """Aggregate statistics across all entries."""
    entries = load_all()
    if not entries:
        return DreamStats()

    all_symbols: list[str] = []
    all_themes: list[str] = []
    mood_counts: Counter = Counter()

    for e in entries:
        if e.interpretation:
            all_symbols.extend(e.interpretation.symbols)
            all_themes.extend(e.interpretation.themes)
            if e.interpretation.mood:
                mood_counts[e.interpretation.mood.lower()] += 1

    stats = DreamStats(
        total_entries=len(entries),
        top_symbols=Counter(all_symbols).most_common(10),
        top_themes=Counter(all_themes).most_common(10),
        mood_distribution=dict(mood_counts.most_common()),
        first_date=entries[-1].date if entries else None,
        last_date=entries[0].date if entries else None,
    )
    return stats