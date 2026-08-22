"""Pydantic models for Echo transcript analysis."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class TranscriptLine(BaseModel):
    """A single line from a conversation transcript."""

    speaker: str = Field(description="Speaker name or label")
    text: str = Field(description="What the speaker said")
    timestamp: Optional[str] = Field(default=None, description="Optional timestamp")


class Transcript(BaseModel):
    """Full conversation transcript."""

    lines: List[TranscriptLine] = Field(description="All lines in order")


class SpeakerStats(BaseModel):
    """Per-speaker statistics."""

    speaker: str
    word_count: int
    turn_count: int
    talk_percentage: float
    filler_word_count: int
    avg_sentence_length: float


class EnergyPoint(BaseModel):
    """An energy/enthusiasm peak in the conversation."""

    speaker: str
    line_index: int
    text: str
    energy_score: float
    reason: str = ""


class RepeatedPhrase(BaseModel):
    """A phrase that appeared multiple times."""

    phrase: str
    count: int
    speakers: List[str]


class AnalysisResult(BaseModel):
    """Complete analysis of a transcript."""

    total_words: int
    total_turns: int
    speakers: List[SpeakerStats]
    filler_word_summary: dict
    filler_words_total: int
    energy_peaks: List[EnergyPoint]
    repeated_phrases: List[RepeatedPhrase]
    longest_turns: List[dict] = Field(default_factory=list)
    shortest_turns: List[dict] = Field(default_factory=list)