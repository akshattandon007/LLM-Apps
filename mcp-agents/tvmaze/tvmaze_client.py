"""
TVMaze API client — wraps the public TVMaze REST API (no key required).
"""

from __future__ import annotations

import httpx
from dataclasses import dataclass, field
from typing import Any

BASE_URL = "https://api.tvmaze.com"

_client: httpx.Client | None = None


def set_client(client: httpx.Client | None) -> None:
    """Inject a mock client for testing."""
    global _client
    _client = client


def _get_client() -> httpx.Client:
    return _client if _client is not None else httpx.Client()


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Show:
    id: int
    name: str
    url: str | None = None
    type: str | None = None
    language: str | None = None
    genres: list[str] = field(default_factory=list)
    status: str | None = None
    runtime: int | None = None
    average_runtime: int | None = None
    premiered: str | None = None
    ended: str | None = None
    official_site: str | None = None
    network: str | None = None
    web_channel: str | None = None
    image_medium: str | None = None
    image_original: str | None = None
    summary: str | None = None
    rating: float | None = None
    weight: int | None = None
    source: str = "live"

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Show":
        network = None
        if d.get("network") and isinstance(d["network"], dict):
            network = d["network"].get("name")
        web_channel = None
        if d.get("webChannel") and isinstance(d["webChannel"], dict):
            web_channel = d["webChannel"].get("name")
        image = d.get("image") or {}
        rating_dict = d.get("rating") or {}
        return cls(
            id=d["id"],
            name=d["name"],
            url=d.get("url"),
            type=d.get("type"),
            language=d.get("language"),
            genres=d.get("genres", []),
            status=d.get("status"),
            runtime=d.get("runtime"),
            average_runtime=d.get("averageRuntime"),
            premiered=d.get("premiered"),
            ended=d.get("ended"),
            official_site=d.get("officialSite"),
            network=network,
            web_channel=web_channel,
            image_medium=image.get("medium"),
            image_original=image.get("original"),
            summary=_strip_html(d.get("summary", "")),
            rating=rating_dict.get("average"),
            weight=d.get("weight"),
        )


@dataclass
class Episode:
    id: int
    name: str
    season: int
    number: int | None = None
    airdate: str | None = None
    airtime: str | None = None
    runtime: int | None = None
    summary: str | None = None
    image_medium: str | None = None
    image_original: str | None = None
    source: str = "live"

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Episode":
        image = d.get("image") or {}
        return cls(
            id=d["id"],
            name=d["name"],
            season=d["season"],
            number=d.get("number"),
            airdate=d.get("airdate"),
            airtime=d.get("airtime"),
            runtime=d.get("runtime"),
            summary=_strip_html(d.get("summary", "")),
            image_medium=image.get("medium"),
            image_original=image.get("original"),
        )


@dataclass
class CastMember:
    person_id: int
    person_name: str
    character_name: str
    character_url: str | None = None
    image_medium: str | None = None
    source: str = "live"

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CastMember":
        person = d.get("person", {})
        character = d.get("character", {})
        image = person.get("image") or {}
        return cls(
            person_id=person.get("id", 0),
            person_name=person.get("name", "Unknown"),
            character_name=character.get("name", "Unknown"),
            character_url=character.get("url"),
            image_medium=image.get("medium"),
        )


@dataclass
class ScheduleItem:
    id: int
    name: str
    airdate: str | None = None
    airtime: str | None = None
    season: int | None = None
    number: int | None = None
    show_name: str | None = None
    show_id: int | None = None
    summary: str | None = None
    source: str = "live"


def _strip_html(text: str | None) -> str | None:
    """Remove basic HTML tags from a string."""
    if not text:
        return text
    import re
    clean = re.sub(r"<[^>]+>", "", text)
    return clean.strip()


# ---------------------------------------------------------------------------
# API calls
# ---------------------------------------------------------------------------

def search_shows(query: str) -> list[Show]:
    """Search for TV shows by name."""
    client = _get_client()
    resp = client.get(f"{BASE_URL}/search/shows", params={"q": query})
    resp.raise_for_status()
    data = resp.json()
    results = []
    for item in data:
        if "show" in item:
            results.append(Show.from_dict(item["show"]))
        else:
            results.append(Show.from_dict(item))
    return results


def get_show_by_id(show_id: int) -> Show:
    """Get detailed info for a specific show by TVMaze ID."""
    client = _get_client()
    resp = client.get(f"{BASE_URL}/shows/{show_id}")
    resp.raise_for_status()
    return Show.from_dict(resp.json())


def get_episodes(show_id: int) -> list[Episode]:
    """Get all episodes for a show (all seasons)."""
    client = _get_client()
    resp = client.get(f"{BASE_URL}/shows/{show_id}/episodes")
    resp.raise_for_status()
    return [Episode.from_dict(e) for e in resp.json()]


def get_cast(show_id: int) -> list[CastMember]:
    """Get the main cast for a show."""
    client = _get_client()
    resp = client.get(f"{BASE_URL}/shows/{show_id}/cast")
    resp.raise_for_status()
    return [CastMember.from_dict(c) for c in resp.json()]


def get_schedule(country: str = "US", date: str | None = None) -> list[ScheduleItem]:
    """Get the TV schedule for a given country and optional date (YYYY-MM-DD)."""
    client = _get_client()
    params: dict[str, str] = {"country": country}
    if date:
        params["date"] = date
    resp = client.get(f"{BASE_URL}/schedule", params=params)
    resp.raise_for_status()
    items = []
    for entry in resp.json():
        show_dict = entry.get("show", {})
        items.append(ScheduleItem(
            id=entry.get("id", 0),
            name=entry.get("name", ""),
            airdate=entry.get("airdate"),
            airtime=entry.get("airtime"),
            season=entry.get("season"),
            number=entry.get("number"),
            show_name=show_dict.get("name"),
            show_id=show_dict.get("id"),
            summary=_strip_html(entry.get("summary", "")),
        ))
    return items


def search_people(query: str) -> list[dict[str, Any]]:
    """Search for people (actors, crew) by name."""
    client = _get_client()
    resp = client.get(f"{BASE_URL}/search/people", params={"q": query})
    resp.raise_for_status()
    return resp.json()


def simulate_search_shows(query: str) -> list[Show]:
    """Simulated fallback when API is unavailable."""
    return [
        Show(
            id=1, name=f"'{query}' — The Series", type="Scripted",
            language="English", genres=["Drama"], status="Running",
            premiered="2020-01-01", summary=f"A fictional show about {query}.",
            rating=7.5, source="simulated",
        ),
        Show(
            id=2, name=f"The {query} Chronicles", type="Reality",
            language="English", genres=["Reality"], status="Ended",
            premiered="2019-06-15", ended="2023-03-10",
            summary=f"A reality series following {query} experts.",
            rating=6.8, source="simulated",
        ),
    ]


def simulate_episodes(show_name: str, season_count: int = 2) -> list[Episode]:
    """Simulated episodes when API is unavailable."""
    eps: list[Episode] = []
    for s in range(1, season_count + 1):
        for ep in range(1, 4):
            eps.append(Episode(
                id=s * 100 + ep,
                name=f"Episode {s}.{ep}",
                season=s,
                number=ep,
                airdate=f"2024-0{s}-0{ep}",
                summary=f"In this episode of {show_name}...",
                source="simulated",
            ))
    return eps