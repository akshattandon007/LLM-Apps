"""Schedule — what's on right now, tonight, and full day."""

from __future__ import annotations

from datetime import datetime, timezone

from .models import ScheduleEntry, Show
from .tvmaze import TVMazeClient


def _format_show_list(shows: list[Show], heading: str = "") -> str:
    """Format a list of shows as a readable string."""
    if not shows:
        return f"{heading}Nothing found for this time slot or criteria.\n"

    lines: list[str] = []
    if heading:
        lines.append(heading)
        lines.append("─" * 60)

    for i, show in enumerate(shows[:20], 1):
        rating = f"{show.rating:.1f}" if show.rating > 0 else "N/A"
        time_str = f" at {show.schedule_time}" if show.schedule_time else ""
        net = f" on {show.network}" if show.network else ""
        genres_str = ", ".join(show.genres[:3]) if show.genres else ""
        summary = show.summary_plain()[:120] if show.summary else ""
        lines.append(
            f"{i:2}. {show.name}{time_str}{net}\n"
            f"    {genres_str:40} ⭐ {rating}\n"
            f"    {summary}\n"
        )

    return "\n".join(lines)


def whats_on_right_now(
    client: TVMazeClient,
    country: str = "US",
    genre: str | None = None,
) -> str:
    """What's airing in the current time slot."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    current_hour = datetime.now(timezone.utc).hour

    entries = client.schedule(country=country, date=today)
    shows: list[Show] = []

    for entry in entries:
        se = ScheduleEntry.from_tvmaze(entry)
        if se.airtime:
            try:
                hour = int(se.airtime.split(":")[0])
            except (ValueError, IndexError):
                continue
            # Shows airing this hour or next (primetime window)
            if current_hour <= hour <= current_hour + 2:
                # Filter by genre if specified
                if genre:
                    norm = genre.strip().lower()
                    show_genres = [g.lower() for g in se.show.genres]
                    if norm not in show_genres and not any(
                        norm in g.lower() for g in show_genres
                    ):
                        continue
                shows.append(se.show)

    heading = (
        f"📺 What's On Right Now ({country.upper()} — {today})\n"
        + (f"   Genre: {genre}" if genre else "")
    )
    return _format_show_list(shows, heading)


def whats_on_tonight(
    client: TVMazeClient,
    genre: str | None = None,
    country: str = "US",
) -> str:
    """Primetime TV schedule for tonight."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entries = client.schedule(country=country, date=today)

    # Primetime = 19:00 - 23:59
    shows: list[Show] = []
    for entry in entries:
        se = ScheduleEntry.from_tvmaze(entry)
        if se.airtime:
            try:
                hour = int(se.airtime.split(":")[0])
            except (ValueError, IndexError):
                continue
            if 19 <= hour <= 23:
                if genre:
                    norm = genre.strip().lower()
                    show_genres = [g.lower() for g in se.show.genres]
                    if norm not in show_genres and not any(
                        norm in g.lower() for g in show_genres
                    ):
                        continue
                shows.append(se.show)

    heading = (
        f"🌙 What's On Tonight ({country.upper()} — Primetime)\n"
        + (f"   Genre: {genre}" if genre else "")
    )
    return _format_show_list(shows, heading)


def daily_schedule(
    client: TVMazeClient,
    date: str | None = None,
    country: str = "US",
) -> str:
    """Full day's TV lineup for a given date."""
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    entries = client.schedule(country=country, date=date)
    shows: list[Show] = []
    for entry in entries:
        se = ScheduleEntry.from_tvmaze(entry)
        shows.append(se.show)

    heading = f"📅 Daily Schedule ({country.upper()} — {date})"
    return _format_show_list(shows, heading)