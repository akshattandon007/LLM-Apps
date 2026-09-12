"""Pydantic models for WhatToWatch data structures."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class Show(BaseModel):
    """A TV show with schedule and metadata."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    url: str | None = None
    genres: list[str] = []
    status: str = "Unknown"
    rating: float = 0.0
    network: str | None = None
    country: str | None = None
    summary: str | None = None
    language: str | None = None
    premiered: str | None = None
    ended: str | None = None
    schedule_time: str | None = None
    schedule_days: list[str] = []

    @classmethod
    def from_tvmaze_show(cls, data: dict[str, Any]) -> "Show":
        """Build a Show from TVMaze show JSON."""
        if not data or "id" not in data:
            return cls(id=0, name="Unknown")
        rating_info = data.get("rating", {}) or {}
        rating = rating_info.get("average") or 0.0
        network_info = data.get("network")
        web_channel = data.get("webChannel")
        network = None
        country = None
        if network_info:
            network = network_info.get("name")
            country = network_info.get("country", {}).get("code")
        elif web_channel:
            network = web_channel.get("name")
        schedule_info = data.get("schedule", {}) or {}
        return cls(
            id=data["id"],
            name=data.get("name", "Unknown"),
            url=data.get("url"),
            genres=data.get("genres", []),
            status=data.get("status", "Unknown"),
            rating=float(rating) if rating else 0.0,
            network=network,
            country=country,
            summary=data.get("summary"),
            language=data.get("language"),
            premiered=data.get("premiered"),
            ended=data.get("ended"),
            schedule_time=schedule_info.get("time"),
            schedule_days=schedule_info.get("days", []),
        )

    @classmethod
    def from_schedule_episode(cls, data: dict[str, Any]) -> "Show":
        """Build a Show from TVMaze schedule episode JSON (nested show)."""
        show_data = data.get("show", data)
        return cls.from_tvmaze_show(show_data)

    def summary_plain(self) -> str:
        """Strip HTML tags from summary."""
        if not self.summary:
            return "No summary available."
        import re
        return re.sub(r"<[^>]+>", "", self.summary).strip()


class ScheduleEntry(BaseModel):
    """A single schedule entry with air time."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    show: Show
    airtime: str | None = None
    airdate: str | None = None
    season: int | None = None
    episode: int | None = None
    name: str | None = None

    @classmethod
    def from_tvmaze(cls, data: dict[str, Any]) -> "ScheduleEntry":
        """Build from TVMaze schedule JSON."""
        return cls(
            id=data.get("id", 0),
            show=Show.from_schedule_episode(data),
            airtime=data.get("airtime"),
            airdate=data.get("airdate"),
            season=data.get("season"),
            episode=data.get("number"),
            name=data.get("name"),
        )