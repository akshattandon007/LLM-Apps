"""Parse TXT, SRT, and VTT transcript files into structured utterances.

Each utterance has: speaker, timestamp_start, timestamp_end, text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


@dataclass
class Utterance:
    speaker: str
    timestamp_start: str
    timestamp_end: str
    text: str


# ── TXT parser (our canonical format) ──────────────────────────────────────

# Matches:  [00:00] Sarah: Hello everyone, let's discuss Q3 pricing
#           [01:23:45] Mike: Some text here
_TXT_LINE_RE = re.compile(
    r"^\[(?P<start>[\d:.]+)\](?:\s*[-–]\s*\[(?P<end>[\d:.]+)\])?\s*"
    r"(?P<speaker>[A-Za-z][A-Za-z0-9_\- ]+?):\s*(?P<text>.+)$"
)


def _parse_timestamp(ts: str) -> str:
    """Normalize a timestamp to HH:MM:SS format."""
    parts = ts.strip().split(":")
    if len(parts) == 2:
        return f"00:{int(parts[0]):02d}:{int(parts[1]):02d}"
    if len(parts) == 3:
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}:{int(parts[2]):02d}"
    return ts


def parse_txt(text: str) -> Iterator[Utterance]:
    """Parse a plain-text transcript with [timestamp] Speaker: text lines."""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = _TXT_LINE_RE.match(line)
        if m:
            start = _parse_timestamp(m.group("start"))
            end_raw = m.group("end")
            end = _parse_timestamp(end_raw) if end_raw else ""
            speaker = m.group("speaker").strip()
            utterance_text = m.group("text").strip()
            yield Utterance(
                speaker=speaker,
                timestamp_start=start,
                timestamp_end=end,
                text=utterance_text,
            )


# ── SRT parser ─────────────────────────────────────────────────────────────

_SRT_TIMESTAMP_RE = re.compile(r"(\d{2}:\d{2}:\d{2}[,.]\d{3})")


def _srt_time_to_hms(s: str) -> str:
    """Convert SRT timestamp (00:01:23,456) to HH:MM:SS."""
    s = s.replace(",", ".") if "," in s else s
    parts = s.strip().split(":")
    if len(parts) == 3:
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}:{int(parts[2].split('.')[0]):02d}"
    return s


def _parse_srt_timestamp_line(line: str):
    """Return (start, end) from an SRT timestamp line like '00:00:01,000 --> 00:00:05,000'."""
    parts = _SRT_TIMESTAMP_RE.findall(line)
    if len(parts) >= 2:
        return _srt_time_to_hms(parts[0]), _srt_time_to_hms(parts[1])
    return "", ""


# Speaker cue patterns for SRT — <v Speaker Name>text</v> or [Speaker Name]
_SRT_SPEAKER_V_TAG = re.compile(r"<v[^>]*\s+([^>]+)>(.*?)</v>", re.DOTALL)
_SRT_SPEAKER_BRACKET = re.compile(r"^\[([^\]]+)\]\s*(.*)")


def parse_srt(text: str) -> Iterator[Utterance]:
    """Parse an SRT subtitle file into utterances."""
    blocks = re.split(r"\n\s*\n", text.strip())
    for block in blocks:
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if len(lines) < 3:
            continue
        # Skip the index line if numeric
        if lines[0].isdigit():
            lines = lines[1:]
        if len(lines) < 2:
            continue
        start, end = _parse_srt_timestamp_line(lines[0])
        content = "\n".join(lines[1:])

        # Try <v Speaker> tag
        v_match = _SRT_SPEAKER_V_TAG.search(content)
        if v_match:
            speaker = v_match.group(1).strip()
            utterance_text = v_match.group(2).strip()
            yield Utterance(
                speaker=speaker,
                timestamp_start=start,
                timestamp_end=end,
                text=utterance_text,
            )
            continue

        # Try [Speaker] prefix
        b_match = _SRT_SPEAKER_BRACKET.match(content)
        if b_match:
            speaker = b_match.group(1).strip()
            utterance_text = b_match.group(2).strip()
            yield Utterance(
                speaker=speaker,
                timestamp_start=start,
                timestamp_end=end,
                text=utterance_text,
            )
            continue

        # Fallback: first line is speaker name (common in simpler SRTs)
        first_line = lines[1]
        if not _SRT_TIMESTAMP_RE.match(first_line) and len(first_line.split()) <= 3:
            speaker = first_line.strip()
            utterance_text = " ".join(lines[2:])
            yield Utterance(
                speaker=speaker,
                timestamp_start=start,
                timestamp_end=end,
                text=utterance_text,
            )
        else:
            # No speaker found — tag as UNKNOWN
            yield Utterance(
                speaker="UNKNOWN",
                timestamp_start=start,
                timestamp_end=end,
                text=content,
            )


# ── VTT parser ─────────────────────────────────────────────────────────────

# VTT format is similar to SRT but uses --> with optional spaces
_VTT_TIMESTAMP_RE = re.compile(r"(\d{2}:\d{2}:\d{2}\.\d{3})")


def _vtt_time_to_hms(s: str) -> str:
    parts = s.strip().split(":")
    if len(parts) == 3:
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}:{int(parts[2].split('.')[0]):02d}"
    return s


def parse_vtt(text: str) -> Iterator[Utterance]:
    """Parse a WebVTT file into utterances."""
    # Strip VTT header
    if text.startswith("WEBVTT"):
        text = text.split("\n", 1)[1] if "\n" in text else ""

    blocks = re.split(r"\n\s*\n", text.strip())
    for block in blocks:
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if len(lines) < 2:
            continue
        # Skip cue identifier if it's not a timestamp line
        if not _VTT_TIMESTAMP_RE.search(lines[0]):
            lines = lines[1:]
        if len(lines) < 2:
            continue
        parts = _VTT_TIMESTAMP_RE.findall(lines[0])
        if len(parts) < 2:
            continue
        start = _vtt_time_to_hms(parts[0])
        end = _vtt_time_to_hms(parts[1])
        content = " ".join(lines[1:])

        # Try <v Speaker> tag
        v_match = _SRT_SPEAKER_V_TAG.search(content)
        if v_match:
            speaker = v_match.group(1).strip()
            utterance_text = v_match.group(2).strip()
        else:
            b_match = _SRT_SPEAKER_BRACKET.match(content)
            if b_match:
                speaker = b_match.group(1).strip()
                utterance_text = b_match.group(2).strip()
            else:
                speaker = "UNKNOWN"
                utterance_text = content

        yield Utterance(
            speaker=speaker,
            timestamp_start=start,
            timestamp_end=end,
            text=utterance_text,
        )


# ── Dispatcher ─────────────────────────────────────────────────────────────

def load_transcript(file_path: str | Path) -> list[Utterance]:
    """Auto-detect format and load a transcript file into utterances.

    Supports: .txt (canonical), .srt, .vtt
    """
    path = Path(file_path)
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()

    if suffix == ".srt":
        utterances = list(parse_srt(text))
    elif suffix == ".vtt":
        utterances = list(parse_vtt(text))
    else:
        utterances = list(parse_txt(text))

    return utterances