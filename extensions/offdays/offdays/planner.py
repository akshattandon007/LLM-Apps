"""Core planner — find optimal leave dates to maximize consecutive time off.

Algorithm:
1. Build a set of all off-days (weekends + public holidays) for the given year.
2. Find maximal consecutive off-day blocks.
3. For each block, compute the gap (consecutive workdays) to the next off block
   on the left and right.
4. For each combination of leave days within those gaps, compute the resulting
   consecutive off stretch (bridging merges adjacent blocks).
5. Return top plans ranked by days_off (desc) then leave_used (asc).
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any


@dataclass
class Plan:
    """A leave plan recommendation."""
    days_off: int
    leave_used: int
    stretch_start: date
    stretch_end: date
    leave_dates: list[date] = field(default_factory=list)
    holidays_covered: list[str] = field(default_factory=list)
    extra_free: int = 0

    def __lt__(self, other):
        return (-self.days_off, self.leave_used) < (-other.days_off, other.leave_used)


@dataclass
class Holiday:
    """A public holiday."""
    date: date
    name: str


def build_off_set(holidays_raw: list[dict], year: int) -> tuple[set[date], list[Holiday]]:
    """Build set of all off-dates and parse holidays for a given year.

    Off-dates = weekends (Sat/Sun) + public holiday dates.
    """
    off: set[date] = set()
    holidays_parsed: list[Holiday] = []

    for h in holidays_raw:
        d = date.fromisoformat(h["date"])
        holidays_parsed.append(Holiday(d, h["name"]))
        off.add(d)

    d = date(year, 1, 1)
    while d.year == year:
        if d.weekday() >= 5:  # Saturday or Sunday
            off.add(d)
        d += timedelta(days=1)

    return off, holidays_parsed


def find_blocks(off: set[date], year: int) -> list[list[date]]:
    """Find maximal consecutive off-day runs in the given year.

    Returns list of blocks, each being a sorted list of consecutive dates.
    """
    sorted_dates = sorted(d for d in off if d.year == year)
    if not sorted_dates:
        return []
    blocks: list[list[date]] = []
    current = [sorted_dates[0]]
    for d in sorted_dates[1:]:
        if d == current[-1] + timedelta(days=1):
            current.append(d)
        else:
            blocks.append(current)
            current = [d]
    blocks.append(current)
    return blocks


def gap_before(off: set[date], start: date) -> list[date]:
    """Return consecutive workdays immediately before block start.

    Returns dates sorted nearest-to-block first.
    Returns empty list if block starts at Jan 1 or is adjacent to another off day.
    """
    gap: list[date] = []
    cursor = start - timedelta(days=1)
    while cursor >= date(start.year, 1, 1) and cursor not in off:
        gap.append(cursor)
        cursor -= timedelta(days=1)
    # gap is built nearest-first (cursor started nearest), no reverse needed
    return gap


def gap_after(off: set[date], end: date) -> list[date]:
    """Return consecutive workdays immediately after block end.

    Returns dates sorted nearest-to-block first.
    Returns empty list if block ends at Dec 31 or is adjacent to another off day.
    """
    gap: list[date] = []
    cursor = end + timedelta(days=1)
    while cursor <= date(end.year, 12, 31) and cursor not in off:
        gap.append(cursor)
        cursor += timedelta(days=1)
    return gap


def compute_plans(
    holidays_raw: list[dict],
    year: int,
    leave_budget: int = 5,
    top_n: int = 10,
) -> list[Plan]:
    """Compute top leave plans for a given set of holidays and leave budget.

    Args:
        holidays_raw: List of dicts from Nager.Date API (or equivalent format).
        year: Calendar year.
        leave_budget: Max leave days to consider (default 5).
        top_n: Max plans to return (default 10).

    Returns:
        List of Plan, ranked by days_off (desc) then leave_used (asc).
    """
    off, holidays = build_off_set(holidays_raw, year)
    holiday_map = {h.date: h.name for h in holidays}
    blocks = find_blocks(off, year)

    plans: list[Plan] = []

    for block in blocks:
        block_start = block[0]
        block_end = block[-1]
        b_len = len(block)

        L_dates = gap_before(off, block_start)  # nearest first
        R_dates = gap_after(off, block_end)     # nearest first
        L = len(L_dates)
        R = len(R_dates)

        # Base case: no leave days — just the free block
        block_holidays = list(dict.fromkeys(
            holiday_map[d] for d in block if d in holiday_map
        ))
        if block_holidays:
            plans.append(Plan(
                days_off=b_len,
                leave_used=0,
                stretch_start=block_start,
                stretch_end=block_end,
                leave_dates=[],
                holidays_covered=block_holidays,
                extra_free=b_len,
            ))

        # Only generate paid-leave plans for blocks that contain a holiday
        if not block_holidays:
            continue

        # Only generate plans if there are gaps to bridge
        if L + R == 0:
            continue

        max_k = min(leave_budget, L + R)
        for k in range(1, max_k + 1):
            min_left = max(0, k - R)
            max_left = min(k, L)
            for kL in range(min_left, max_left + 1):
                kR = k - kL

                # Booked leave dates
                booked: set[date] = set()
                if kL > 0:
                    booked.update(L_dates[:kL])
                if kR > 0:
                    booked.update(R_dates[:kR])

                # Compute the maximal stretch containing this block
                total_off = off | booked
                sorted_total = sorted(d for d in total_off if d.year == year)

                # Find run containing block_start
                stretch_dates: list[date] = []
                current_run: list[date] = []
                for d in sorted_total:
                    if not current_run:
                        current_run = [d]
                    elif d == current_run[-1] + timedelta(days=1):
                        current_run.append(d)
                    else:
                        if block_start in current_run:
                            stretch_dates = current_run
                            break
                        current_run = [d]
                else:
                    if block_start in current_run:
                        stretch_dates = current_run

                if not stretch_dates:
                    continue

                stretch_len = len(stretch_dates)
                stretch_start = stretch_dates[0]
                stretch_end = stretch_dates[-1]

                # Holidays covered in stretch
                covered = list(dict.fromkeys(
                    holiday_map.get(d) for d in stretch_dates
                    if d in holiday_map
                ))

                plans.append(Plan(
                    days_off=stretch_len,
                    leave_used=k,
                    stretch_start=stretch_start,
                    stretch_end=stretch_end,
                    leave_dates=sorted(booked),
                    holidays_covered=covered,
                    extra_free=stretch_len - k,
                ))

    # Deduplicate: same stretch + same leave_used → keep first
    seen: dict[tuple[int, int, int], Plan] = {}  # (start_ord, end_ord, leave_used) -> Plan
    for p in plans:
        key = (p.stretch_start.toordinal(), p.stretch_end.toordinal(), p.leave_used)
        if key not in seen:
            seen[key] = p
        else:
            # Keep plan with fewer holidays-covered? No — keep the one with lower holidays
            # Actually just keep first
            pass

    # Rank: days_off desc, leave_used asc
    ranked = sorted(seen.values(), key=lambda p: (-p.days_off, p.leave_used))
    return ranked[:top_n]