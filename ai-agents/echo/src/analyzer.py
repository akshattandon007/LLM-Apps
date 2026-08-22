"""Transcript analyzer — word counts, filler words, talk ratio, sentence stats."""

from __future__ import annotations

import re
from collections import Counter

from .models import AnalysisResult, SpeakerStats, Transcript, TranscriptLine

# Common filler words in conversational speech
FILLER_WORDS = {
    "actually",
    "like",
    "you know",
    "um",
    "uh",
    "well",
    "so",
    "basically",
    "literally",
    "honestly",
    "right",
    "okay",
    "i mean",
    "sort of",
    "kind of",
    "you see",
    "anyway",
}

# Words that strongly indicate hedging or filler
FILLER_UNIGRAMS = {"actually", "like", "um", "uh", "well", "basically", "literally", "honestly", "okay"}


def _count_filler_words(text: str) -> int:
    """Count filler words in a line of text."""
    lower = text.lower()
    count = 0

    # Multi-word fillers first
    for phrase in ["you know", "i mean", "sort of", "kind of", "you see"]:
        count += len(re.findall(rf"\b{re.escape(phrase)}\b", lower))

    # Single-word fillers
    for word in FILLER_UNIGRAMS:
        count += len(re.findall(rf"\b{re.escape(word)}\b", lower))

    return count


def _word_count(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def _sentence_count(text: str) -> int:
    """Count sentences (split on .!?)."""
    sentences = re.split(r"[.!?]+", text)
    return len([s for s in sentences if s.strip()])


def _avg_sentence_length(text: str) -> float:
    """Average words per sentence."""
    words = text.split()
    n_words = len(words)
    if n_words == 0:
        return 0.0
    sentences = _sentence_count(text)
    if sentences == 0:
        return float(n_words)
    return round(n_words / sentences, 1)


def analyze(transcript: Transcript) -> AnalysisResult:
    """Run full analysis on a transcript."""
    lines = transcript.lines
    total_turns = len(lines)
    speaker_lines: dict[str, list[str]] = {}
    speaker_turns: dict[str, int] = Counter()

    for line in lines:
        speaker = line.speaker
        if speaker not in speaker_lines:
            speaker_lines[speaker] = []
        speaker_lines[speaker].append(line.text)
        speaker_turns[speaker] += 1

    # Total words
    all_text = " ".join(line.text for line in lines)
    total_words = _word_count(all_text)

    # Per-speaker stats
    speaker_stats_list: list[SpeakerStats] = []
    for speaker, texts in speaker_lines.items():
        combined = " ".join(texts)
        wc = _word_count(combined)
        turns = speaker_turns[speaker]
        fw = sum(_count_filler_words(t) for t in texts)
        talk_pct = round(wc / total_words * 100, 1) if total_words else 0.0
        asl = _avg_sentence_length(combined)

        speaker_stats_list.append(
            SpeakerStats(
                speaker=speaker,
                word_count=wc,
                turn_count=turns,
                talk_percentage=talk_pct,
                filler_word_count=fw,
                avg_sentence_length=asl,
            )
        )

    # Sort by word_count descending (most talkative first)
    speaker_stats_list.sort(key=lambda s: s.word_count, reverse=True)

    # Filler word summary — total per filler type
    filler_counter: Counter = Counter()
    for line in lines:
        lower = line.text.lower()
        for phrase in ["you know", "i mean", "sort of", "kind of", "you see"]:
            cnt = len(re.findall(rf"\b{re.escape(phrase)}\b", lower))
            if cnt:
                filler_counter[phrase] += cnt
        for word in FILLER_UNIGRAMS:
            cnt = len(re.findall(rf"\b{re.escape(word)}\b", lower))
            if cnt:
                filler_counter[word] += cnt

    filler_words_total = sum(filler_counter.values())

    # Longest and shortest turns
    turn_word_counts = [(i, line.speaker, _word_count(line.text)) for i, line in enumerate(lines)]
    turn_word_counts.sort(key=lambda x: x[2], reverse=True)
    longest_turns = [
        {
            "line_index": idx,
            "speaker": spk,
            "word_count": wc,
            "text": lines[idx].text[:120],
        }
        for idx, spk, wc in turn_word_counts[:3]
    ]
    shortest_turns = [
        {
            "line_index": idx,
            "speaker": spk,
            "word_count": wc,
            "text": lines[idx].text[:120],
        }
        for idx, spk, wc in turn_word_counts[-3:] if wc > 0
    ]

    return AnalysisResult(
        total_words=total_words,
        total_turns=total_turns,
        speakers=speaker_stats_list,
        filler_word_summary=dict(filler_counter.most_common(10)),
        filler_words_total=filler_words_total,
        energy_peaks=[],  # filled by patterns module
        repeated_phrases=[],  # filled by patterns module
        longest_turns=longest_turns,
        shortest_turns=shortest_turns,
    )