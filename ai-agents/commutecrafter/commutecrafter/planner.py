"""The planner: fit content to an exact commute window.

Design in one sentence: split the window into three acts, best-fit real content
into each act's budget, then balance the total so the plan ends within the
tolerance instead of 20 minutes into a podcast you cannot finish.
"""

from __future__ import annotations

from typing import Iterable, Sequence

from .models import (
    ContentItem,
    Plan,
    ScheduledItem,
    SEGMENT_CORE,
    SEGMENT_ORDER,
    SEGMENT_WARMUP,
    SEGMENT_WINDDOWN,
    Segment,
)
from .timing import (
    DEFAULT_PROFILE,
    ITEM_OVERHEAD_SECONDS,
    PacingProfile,
    clamp_minutes,
    estimate_seconds,
    wpm_for_mode,
)

#: Never lean on one source for the whole commute.
MAX_PER_SOURCE = 2

#: How many pieces each act may contain. Long commutes still read as three acts.
MAX_ITEMS_PER_SEGMENT: dict[str, int] = {
    SEGMENT_WARMUP: 3,
    SEGMENT_CORE: 3,
    SEGMENT_WINDDOWN: 2,
}

#: Category words that suit each act.
PREFERRED_CATEGORIES: dict[str, set[str]] = {
    SEGMENT_WARMUP: {"news", "culture", "general"},
    SEGMENT_CORE: {"deep", "long", "news", "culture", "general"},
    SEGMENT_WINDDOWN: {"reflective", "culture", "general"},
}

#: Upper bound on a single item's share of an act, so warm-up stays short.
SEGMENT_MAX_SECONDS: dict[str, int] = {
    SEGMENT_WARMUP: 5 * 60,
    SEGMENT_CORE: 60 * 60,
    SEGMENT_WINDDOWN: 12 * 60,
}

#: A partial item below this fraction is not worth opening at all.
MIN_PARTIAL_FRACTION = 0.35

#: Do not bother padding with something shorter than this.
MIN_PADDING_SECONDS = 45

#: Below this, an item is dropped rather than trimmed to a sliver.
MIN_TRIM_SECONDS = 30


def _duration(item: ContentItem, wpm: int) -> int:
    return estimate_seconds(item.words, wpm, ITEM_OVERHEAD_SECONDS)


def _rescale(scheduled: ScheduledItem, seconds: int, wpm: int) -> ScheduledItem:
    """Shrink a scheduled item to ``seconds``, keeping a consistent fraction."""
    full = max(1, _duration(scheduled.item, wpm))
    fraction = max(0.01, min(1.0, seconds / full))
    new_seconds = estimate_seconds(int(scheduled.item.words * fraction), wpm, ITEM_OVERHEAD_SECONDS)
    return ScheduledItem(
        item=scheduled.item,
        seconds=min(seconds, new_seconds) if new_seconds else new_seconds,
        segment=scheduled.segment,
        fraction=fraction,
        reason=scheduled.reason,
    )


def _score(item: ContentItem, segment: str) -> int:
    """Higher is better. Preference first, then substance."""
    pref = 1 if item.category in PREFERRED_CATEGORIES[segment] else 0
    return pref * 1000 + min(item.words, 900)


def _candidates(
    items: Sequence[ContentItem],
    segment: str,
    wpm: int,
    exclude_urls: set[str],
) -> list[tuple[ContentItem, int]]:
    max_seconds = SEGMENT_MAX_SECONDS[segment]
    out: list[tuple[ContentItem, int]] = []
    for item in items:
        if item.url in exclude_urls:
            continue
        dur = _duration(item, wpm)
        if dur < 20 or dur > max_seconds:
            continue
        out.append((item, dur))
    out.sort(key=lambda pair: (-_score(pair[0], segment), pair[1], pair[0].title))
    return out


def _source_counts(scheduled: Iterable[ScheduledItem]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for s in scheduled:
        counts[s.item.source] = counts.get(s.item.source, 0) + 1
    return counts


def _fill_segment(
    segment: str,
    budget: int,
    items: Sequence[ContentItem],
    wpm: int,
    used_titles: set[str],
    source_counts: dict[str, int],
    tolerance: int,
) -> list[ScheduledItem]:
    """Best-fit content into one act's budget."""
    remaining = budget
    slack = max(20, tolerance // 3)
    chosen: list[ScheduledItem] = []
    pool = [c for c in _candidates(items, segment, wpm, set()) if c[0].title not in used_titles]

    while len(chosen) < MAX_ITEMS_PER_SEGMENT[segment] and remaining >= MIN_PADDING_SECONDS:
        viable = [
            (item, dur)
            for item, dur in pool
            if item.title not in used_titles
            and source_counts.get(item.source, 0) < MAX_PER_SOURCE
            and dur <= remaining + slack
        ]
        if not viable:
            break
        # Prefer the piece that leaves the least dead air, then the richer one.
        item, dur = min(viable, key=lambda p: (abs(remaining - p[1]), -p[1]))
        chosen.append(
            ScheduledItem(
                item=item,
                seconds=dur,
                segment=segment,
                fraction=1.0,
                reason=f"{item.source} · {item.words} words",
            )
        )
        used_titles.add(item.title)
        source_counts[item.source] = source_counts.get(item.source, 0) + 1
        remaining -= dur
    return chosen


def build_plan(
    items: Sequence[ContentItem],
    minutes: float,
    *,
    mode: str = "read",
    profile: PacingProfile | None = None,
    tolerance: int = 90,
    exclude_urls: Iterable[str] | None = None,
    transport: str | None = None,
    weather: dict | None = None,
    warnings: list[str] | None = None,
) -> Plan:
    """Build a pacing-aware plan that fits ``minutes`` within ``tolerance``.

    ``items`` should already be deduplicated and ranked by relevance.
    ``exclude_urls`` filters out anything recently served, which is what stops
    the same Wikipedia article showing up every morning.
    """
    minutes = clamp_minutes(minutes)
    profile = profile or DEFAULT_PROFILE
    wpm = wpm_for_mode(mode)
    target = int(round(minutes * 60))
    exclude = {u.strip().lower() for u in (exclude_urls or ()) if u}
    warnings = warnings if warnings is not None else []

    unique: list[ContentItem] = []
    seen: set[str] = set()
    for item in items or ():
        key = item.url.strip().lower()
        if not key or key in seen or key in exclude:
            continue
        seen.add(key)
        unique.append(item)

    budgets = profile.budgets(target)

    used_titles: set[str] = set()
    source_counts: dict[str, int] = {}
    segments: list[Segment] = []
    for name in SEGMENT_ORDER:
        picked = _fill_segment(
            name, budgets[name], unique, wpm, used_titles, source_counts, tolerance
        )
        segments.append(Segment(name=name, budget_seconds=budgets[name], items=picked))

    # --- Balance ------------------------------------------------------------
    # Pad when short, trim when long, and re-check: a trim can undershoot, and
    # an undershoot can be padded again. Five passes is plenty in practice.
    core_seg = next((s for s in segments if s.name == SEGMENT_CORE), None)
    for _ in range(5):
        total = sum(s.seconds for s in segments)
        if total > target + tolerance:
            _trim_once(segments, total - (target + tolerance), wpm)
        elif total < target - tolerance:
            if not _pad_once(
                segments, core_seg, unique, used_titles, source_counts, wpm,
                target - total, tolerance,
            ):
                warnings.append(
                    f"Only {total}s of fitting content available for a {target}s window."
                )
                break
        else:
            break

    segments = [s for s in segments if s.items]

    return Plan(
        minutes=minutes,
        mode=mode,
        segments=segments,
        tolerance_seconds=tolerance,
        weather=weather,
        transport=transport,
        warnings=warnings,
    )


def _pad_once(
    segments: list[Segment],
    core_seg: Segment | None,
    items: Sequence[ContentItem],
    used_titles: set[str],
    source_counts: dict[str, int],
    wpm: int,
    gap: int,
    tolerance: int,
) -> bool:
    """Add one item to absorb ``gap`` seconds. Returns False if impossible."""
    if gap < MIN_PADDING_SECONDS or not segments:
        return False
    padding = _best_padding(items, used_titles, source_counts, wpm, gap, tolerance)
    if padding is None:
        # Source diversity is a preference, not a reason to leave the commuter
        # with ten minutes of silence.
        padding = _best_padding(
            items, used_titles, source_counts, wpm, gap, tolerance, respect_caps=False
        )
    if padding is None:
        return False
    target_seg = core_seg if core_seg is not None else segments[-1]
    target_seg.items.append(padding)
    used_titles.add(padding.item.title)
    source_counts[padding.item.source] = source_counts.get(padding.item.source, 0) + 1
    return True


def _trim_once(segments: list[Segment], over: int, wpm: int) -> None:
    """Remove ``over`` seconds, trimming the core first and the landing last."""
    order = [SEGMENT_CORE, SEGMENT_WARMUP, SEGMENT_WINDDOWN]
    ordered = sorted(
        segments, key=lambda seg: order.index(seg.name) if seg.name in order else 99
    )
    for seg in ordered:
        if over <= 0:
            break
        while seg.items and over > 0:
            sched = seg.items[-1]
            keep = sched.seconds - over
            if keep < MIN_TRIM_SECONDS:
                over -= sched.seconds
                seg.items.pop()
                continue
            shrunk = _rescale(sched, keep, wpm)
            consumed = sched.seconds - shrunk.seconds
            if consumed <= 0:  # pragma: no cover - guard against rounding stalls
                over -= sched.seconds
                seg.items.pop()
                continue
            over -= consumed
            seg.items[-1] = shrunk


def _best_padding(
    items: Sequence[ContentItem],
    used_titles: set[str],
    source_counts: dict[str, int],
    wpm: int,
    gap: int,
    tolerance: int,
    respect_caps: bool = True,
) -> ScheduledItem | None:
    """Fill leftover time with the best unused item, trimmed to fit."""
    pool = [
        (item, _duration(item, wpm))
        for item in items
        if item.title not in used_titles
        and (not respect_caps or source_counts.get(item.source, 0) < MAX_PER_SOURCE)
    ]
    pool = [p for p in pool if p[1] >= MIN_PADDING_SECONDS]
    if not pool:
        return None
    pool.sort(key=lambda p: (abs(p[1] - gap), -p[1]))
    item, dur = pool[0]
    take = min(dur, gap)
    fraction = take / max(1, dur)
    if fraction < MIN_PARTIAL_FRACTION:
        return None
    seconds = estimate_seconds(int(item.words * fraction), wpm, ITEM_OVERHEAD_SECONDS)
    return ScheduledItem(
        item=item,
        seconds=min(take, seconds) if seconds else seconds,
        segment=SEGMENT_CORE,
        fraction=fraction,
        reason=f"{item.source} · trimmed to fit · {int(fraction * 100)}% of {item.words} words",
    )


def format_gap(seconds: int) -> str:
    return f"{max(0, int(seconds))}"
