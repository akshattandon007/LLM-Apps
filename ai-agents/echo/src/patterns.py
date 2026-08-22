"""Pattern detection — energy peaks, repeated phrases, interruptions."""

from __future__ import annotations

import re
from collections import Counter
from itertools import combinations

from .models import AnalysisResult, EnergyPoint, RepeatedPhrase, Transcript

# Words/phrasing that suggest enthusiasm
ENERGY_KEYWORDS = {
    "amazing", "awesome", "incredible", "wow", "love", "great",
    "fantastic", "brilliant", "exciting", "omg", "so good",
    "hilarious", "perfect", "best", "unbelievable",
}

# Punctuation that adds energy
ENERGY_PUNCTUATION = re.compile(r"[!?]+")


def detect_energy_peaks(transcript: Transcript) -> list[EnergyPoint]:
    """Score each line for energy/enthusiasm and return top peaks."""
    scored: list[tuple[int, float, str]] = []

    for i, line in enumerate(transcript.lines):
        text = line.text.strip()
        if not text:
            continue

        score = 0.0

        # Exclamation/question marks
        excl = ENERGY_PUNCTUATION.findall(text)
        score += len(excl) * 2.0

        # All-caps words (shouting/excitement)
        caps_words = len(re.findall(r"\b[A-Z]{2,}\b", text))
        score += caps_words * 1.5

        # Energy keywords
        lower = text.lower()
        for kw in ENERGY_KEYWORDS:
            if kw in lower:
                score += 2.0

        # Short enthusiastic lines — "Wow!" "No way!"
        word_count = len(text.split())
        if word_count <= 5 and score > 0:
            score += 1.0

        if score > 0:
            scored.append((i, score, text))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:5]

    reasons = []
    for idx, score, text in top:
        parts = []
        if "!" in text:
            parts.append("exclamation mark")
        if any(kw in text.lower() for kw in ENERGY_KEYWORDS):
            parts.append("enthusiastic language")
        if re.findall(r"\b[A-Z]{2,}\b", text):
            parts.append("emphasis via caps")
        reason = " + ".join(parts) if parts else "positive/surprised tone"
        reasons.append(
            EnergyPoint(
                speaker=transcript.lines[idx].speaker,
                line_index=idx,
                text=text[:120],
                energy_score=round(score, 1),
                reason=reason,
            )
        )

    return reasons


def detect_repeated_phrases(transcript: Transcript, min_count: int = 2) -> list[RepeatedPhrase]:
    """Find repeated 2- to 4-word phrases across the transcript."""
    all_text = " ".join(line.text for line in transcript.lines)
    lower = all_text.lower()
    # Remove punctuation for matching
    words = re.findall(r"\b[a-z']+\b", lower)
    n = len(words)

    phrase_counts: Counter = Counter()

    # N-grams: 2-, 3-word phrases
    for gram_len in [2, 3]:
        for start in range(n - gram_len + 1):
            phrase = " ".join(words[start : start + gram_len])
            if len(phrase) > 3:  # skip tiny fragments
                phrase_counts[phrase] += 1

    # Filter by min_count
    candidates = [(p, c) for p, c in phrase_counts.items() if c >= min_count]
    candidates.sort(key=lambda x: x[1], reverse=True)

    # Deduplicate: skip phrases that are substrings of longer ones
    filtered = []
    for phrase, count in candidates:
        is_sub = any(phrase in existing for existing, _ in filtered)
        if not is_sub:
            filtered.append((phrase, count))
        if len(filtered) >= 5:
            break

    # Find which speakers used each phrase
    result = []
    for phrase, count in filtered:
        speakers = set()
        for line in transcript.lines:
            if phrase in line.text.lower():
                speakers.add(line.speaker)
        result.append(
            RepeatedPhrase(
                phrase=phrase,
                count=count,
                speakers=sorted(speakers),
            )
        )

    return result


def detect_interruptions(transcript: Transcript) -> dict:
    """Detect possible interruptions — very short turns after long ones."""
    interruptions = []
    for i in range(1, len(transcript.lines)):
        prev = transcript.lines[i - 1]
        curr = transcript.lines[i]
        if prev.speaker != curr.speaker:
            prev_wc = len(prev.text.split())
            curr_wc = len(curr.text.split())
            # If previous turn was substantive and current is short (<5 words)
            # and the current speaker is different, it might be an interruption
            if prev_wc > 15 and curr_wc <= 4:
                interruptions.append(
                    {
                        "interrupted": prev.speaker,
                        "interrupter": curr.speaker,
                        "interrupted_text": prev.text[:80],
                        "interruption_text": curr.text[:80],
                        "line_index": i,
                    }
                )

    return {
        "interruption_count": len(interruptions),
        "interruptions": interruptions[:5],
    }