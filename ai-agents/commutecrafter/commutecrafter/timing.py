"""Time arithmetic: words <-> seconds, and how to slice a commute window.

The whole app exists because content is sold in fixed doses ("a 47 minute
podcast") while commutes are arbitrary ("22 minutes, and 3 of those are
walking"). These are the pure functions that make that conversion honest.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

#: Words per minute for silent reading of web prose.
READ_WPM = 230

#: Words per minute for narration / audiobook playback at 1.0x speed.
LISTEN_WPM = 150

#: Friction per item: unlocking the phone, finding the tab, queueing audio.
ITEM_OVERHEAD_SECONDS = 8

#: Absolute bounds for a sane commute window.
MIN_MINUTES = 2.0
MAX_MINUTES = 240.0


def wpm_for_mode(mode: str) -> int:
    """Pick a words-per-minute rate for ``mode`` ('read' or 'listen')."""
    return LISTEN_WPM if str(mode).lower() in {"listen", "audio", "podcast"} else READ_WPM


def estimate_seconds(words: int, wpm: int, overhead: int = 0) -> int:
    """Seconds needed to consume ``words`` words at ``wpm``.

    Always at least one second for any non-zero word count: a 3 word headline
    still costs attention.
    """
    if words <= 0:
        return 0
    if wpm <= 0:
        raise ValueError("wpm must be positive")
    return max(1, math.ceil(words / wpm * 60)) + max(0, overhead)


def words_for_seconds(seconds: int, wpm: int) -> int:
    """Inverse of :func:`estimate_seconds` (ignores overhead)."""
    if seconds <= 0:
        return 0
    if wpm <= 0:
        raise ValueError("wpm must be positive")
    return max(1, int(round(seconds / 60 * wpm)))


def clamp_minutes(minutes: float) -> float:
    """Keep a commute window inside something a human would recognise."""
    try:
        value = float(minutes)
    except (TypeError, ValueError):
        raise ValueError(f"minutes must be a number, got {minutes!r}") from None
    if value != value or value in (float("inf"), float("-inf")):
        raise ValueError("minutes must be finite")
    return max(MIN_MINUTES, min(MAX_MINUTES, value))


def format_duration(seconds: int) -> str:
    """Render seconds as ``m:ss`` (or ``h:mm:ss`` past the hour)."""
    seconds = max(0, int(round(seconds)))
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{sec:02d}"
    return f"{minutes}:{sec:02d}"


@dataclass(frozen=True)
class PacingProfile:
    """How to split a commute across its three acts.

    Based on the widely used podcast pacing convention: open light, go deep in
    the middle, land gently so you arrive composed rather than mid-thought.
    """

    warmup: float = 0.18
    core: float = 0.62
    winddown: float = 0.20

    def __post_init__(self) -> None:
        total = self.warmup + self.core + self.winddown
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"pacing shares must sum to 1.0, got {total}")

    def budgets(self, total_seconds: int) -> dict[str, int]:
        """Split ``total_seconds`` into warm-up / core / wind-down budgets.

        Rounding residue is pushed into ``core`` so the three budgets always
        sum exactly to the total.
        """
        total_seconds = max(0, int(total_seconds))
        warm = int(round(total_seconds * self.warmup))
        wind = int(round(total_seconds * self.winddown))
        core = total_seconds - warm - wind
        return {"warm-up": warm, "core": core, "wind-down": wind}


DEFAULT_PROFILE = PacingProfile()
