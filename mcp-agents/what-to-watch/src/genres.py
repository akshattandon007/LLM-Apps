"""Genre definitions and show discovery."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .tvmaze import TVMazeClient

# Canonical genre mapping — TVMaze uses these exact strings
# https://www.tvmaze.com/api#show-index
GENRES = [
    "Action",
    "Adult",
    "Adventure",
    "Animation",
    "Anime",
    "Children",
    "Comedy",
    "Crime",
    "DIY",
    "Drama",
    "Documentary",
    "Educational",
    "Entertainment",
    "Fantasy",
    "Food",
    "History",
    "Horror",
    "Legal",
    "Medical",
    "Music",
    "Mystery",
    "Nature",
    "Reality",
    "Romance",
    "Science-Fiction",
    "Sport",
    "Supernatural",
    "Suspense",
    "Talk Show",
    "Thriller",
    "Travel",
    "War",
    "Western",
]

# Friendly groupings for user-facing prompts
GENRE_GROUPINGS: dict[str, list[str]] = {
    "comedy": ["Comedy", "Anime"],
    "drama": ["Drama", "Romance", "Medical", "Legal"],
    "cooking": ["Food", "DIY"],
    "reality": ["Reality", "Entertainment", "Talk Show"],
    "sport": ["Sport"],
    "sci-fi": ["Science-Fiction", "Fantasy", "Adventure"],
    "news": ["Educational", "History"],
    "documentary": ["Nature", "History", "Travel"],
    "scifi": ["Science-Fiction", "Fantasy", "Adventure"],
    "thriller": ["Thriller", "Suspense", "Mystery", "Horror", "Crime"],
    "crime": ["Crime", "Legal", "Thriller"],
    "animation": ["Animation", "Anime", "Children"],
    "action": ["Action", "Adventure", "War", "Western"],
}


def normalize_genre_input(user_input: str) -> list[str]:
    """Map user-friendly genre input to TVMaze genre strings."""
    key = user_input.strip().lower()
    if key in GENRE_GROUPINGS:
        return GENRE_GROUPINGS[key]
    # Check if it's an exact TVMaze genre
    for g in GENRES:
        if g.lower() == key:
            return [g]
    # Partial match
    matches = [g for g in GENRES if key in g.lower()]
    if matches:
        return matches
    return []


def discover_by_genre(
    client: TVMazeClient,
    genres: list[str],
    limit: int = 10,
) -> list[dict]:
    """Discover shows matching given genres by scanning TVMaze show index."""
    seen_ids: set[int] = set()
    results: list[dict] = []
    page = 0
    max_pages = 20  # safety limit
    while len(results) < limit and page < max_pages:
        try:
            shows = client.shows_page(page)
        except Exception:
            break
        if not shows:
            break
        for show in shows:
            if show["id"] in seen_ids:
                continue
            seen_ids.add(show["id"])
            show_genres = [g.lower() for g in show.get("genres", [])]
            target_genres = [g.lower() for g in genres]
            if any(tg in show_genres for tg in target_genres):
                # Only add if it has a reasonable rating
                rating = show.get("rating", {}) or {}
                if rating.get("average"):
                    results.append(show)
                    if len(results) >= limit:
                        break
        page += 1
    return results[:limit]