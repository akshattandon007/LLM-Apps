"""Search shows by name, genre, rating."""

from __future__ import annotations

from .genres import GENRE_GROUPINGS, normalize_genre_input
from .models import Show
from .tvmaze import TVMazeClient


def search_show(
    client: TVMazeClient,
    query: str,
) -> str:
    """Search for a show by name."""
    results = client.search_show(query)
    if not results:
        return f"❌ No shows found for '{query}'."

    lines: list[str] = [f"🔍 Search results for '{query}':", "─" * 60]
    for i, item in enumerate(results[:15], 1):
        show_data = item.get("show", item)
        show = Show.from_tvmaze_show(show_data)
        rating = f"{show.rating:.1f}" if show.rating > 0 else "N/A"
        net = f" on {show.network}" if show.network else ""
        genres_str = ", ".join(show.genres[:4]) if show.genres else "No genres"
        status = show.status
        summary = show.summary_plain()[:150] if show.summary else ""
        lines.append(
            f"{i:2}. {show.name}{net}\n"
            f"    {genres_str:45} ⭐ {rating}  [{status}]\n"
            f"    {summary}\n"
        )

    return "\n".join(lines)


def search_by_genre(
    client: TVMazeClient,
    genre: str,
    limit: int = 10,
) -> str:
    """Discover shows by genre."""
    from .genres import discover_by_genre

    target_genres = normalize_genre_input(genre)
    if not target_genres:
        return (
            f"❌ Unknown genre '{genre}'. "
            f"Try: {', '.join(sorted(GENRE_GROUPINGS.keys()))}"
        )

    results = discover_by_genre(client, target_genres, limit=limit)
    if not results:
        return (
            f"❌ No shows found for genre '{genre}' (mapped to: {target_genres})."
        )

    lines: list[str] = [
        f"🎭 Top shows in '{genre}' (mapped to: {', '.join(target_genres)}):",
        "─" * 60,
    ]
    for i, show_data in enumerate(results, 1):
        show = Show.from_tvmaze_show(show_data)
        rating = f"{show.rating:.1f}" if show.rating > 0 else "N/A"
        net = f" on {show.network}" if show.network else ""
        genres_str = ", ".join(show.genres[:4]) if show.genres else ""
        summary = show.summary_plain()[:120] if show.summary else ""
        lines.append(
            f"{i:2}. {show.name}{net}\n"
            f"    {genres_str:45} ⭐ {rating}\n"
            f"    {summary}\n"
        )
    return "\n".join(lines)