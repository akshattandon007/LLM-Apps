"""Similar show recommendations — genre-based + rating."""

from __future__ import annotations

from .models import Show
from .tvmaze import TVMazeClient


def find_similar_shows(
    client: TVMazeClient,
    show_name: str,
    limit: int = 8,
) -> str:
    """Find shows similar to one you love."""
    source_show = client.show_by_name(show_name)
    if not source_show:
        return f"❌ Could not find show '{show_name}' on TVMaze."

    source = Show.from_tvmaze_show(source_show)
    source_genres = [g.lower() for g in source.genres]
    source_rating = source.rating

    if not source_genres:
        return f"❌ '{show_name}' has no genre information — can't find similar shows."

    # Scan pages for shows sharing at least one genre
    from .genres import discover_by_genre

    candidates = discover_by_genre(client, source_genres, limit=30)

    # Score and rank candidates
    scored: list[tuple[float, Show]] = []
    for candidate_data in candidates:
        candidate = Show.from_tvmaze_show(candidate_data)
        if candidate.name.lower() == show_name.lower():
            continue  # skip self

        candidate_genres = [g.lower() for g in candidate.genres]

        # Genre overlap score
        overlap = len(set(source_genres) & set(candidate_genres))
        if overlap == 0:
            continue

        # Rating proximity (lower delta = better)
        rating_delta = abs(candidate.rating - source_rating) if source_rating > 0 else 0
        rating_score = max(0, 10 - rating_delta)

        total = (overlap * 3) + rating_score
        scored.append((total, candidate))

    scored.sort(key=lambda x: x[0], reverse=True)

    lines: list[str] = [
        f"🎬 If you like '{show_name}', try these:",
        "─" * 60,
    ]
    for i, (score, show) in enumerate(scored[:limit], 1):
        rating = f"{show.rating:.1f}" if show.rating > 0 else "N/A"
        net = f" on {show.network}" if show.network else ""
        genres_str = ", ".join(show.genres[:4]) if show.genres else ""
        summary = show.summary_plain()[:120] if show.summary else ""
        lines.append(
            f"{i:2}. {show.name}{net}\n"
            f"    {genres_str:45} ⭐ {rating}\n"
            f"    {summary}\n"
        )

    if len(lines) == 1:
        return f"❌ No similar shows found for '{show_name}'."

    return "\n".join(lines)