"""Chunk utterances into indexed documents.

Each utterance becomes one chunk with:
  - Speaker name prepended: '[Sarah] The pricing model should be usage-based.'
  - Metadata: meeting_title, meeting_date, speaker, timestamp_start, timestamp_end
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.document_loader import Utterance


@dataclass
class Chunk:
    id: str
    text: str  # '[Speaker] utterance text'
    metadata: dict
    embedding: Optional[list[float]] = None


def chunk_utterances(
    utterances: list[Utterance],
    meeting_title: str = "Untitled Meeting",
    meeting_date: str = "",
    source_file: str = "",
) -> list[Chunk]:
    """Convert a list of utterances into Chunk objects.

    Each utterance becomes one chunk. Speaker name is prepended to the text
    so it's present in the embedding space for speaker-attributed retrieval.
    """
    chunks: list[Chunk] = []
    for i, utt in enumerate(utterances):
        prepended_text = f"[{utt.speaker}] {utt.text}"
        metadata = {
            "speaker": utt.speaker,
            "timestamp_start": utt.timestamp_start,
            "timestamp_end": utt.timestamp_end,
            "text": utt.text,  # original text without prepended speaker
            "meeting_title": meeting_title,
            "meeting_date": meeting_date,
            "source_file": source_file,
        }
        chunk = Chunk(
            id=f"{source_file or 'transcript'}_{i:04d}",
            text=prepended_text,
            metadata=metadata,
        )
        chunks.append(chunk)

    return chunks