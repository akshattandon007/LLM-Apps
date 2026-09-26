"""LLM-powered mixtape curator — turns mood + tracks into a themed playlist."""

from __future__ import annotations

import json
import os
from typing import Optional

from openai import OpenAI

from .models import Mixtape, MixtapeSong, Track

# Default LLM config
_DEFAULT_MODEL = "deepseek/deepseek-v4-flash"
_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


def _get_openai_client() -> OpenAI:
    """Get an OpenAI-compatible client configured for the available LLM."""
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY") or "sk-placeholder"
    base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENROUTER_BASE_URL") or _DEFAULT_BASE_URL
    return OpenAI(api_key=api_key, base_url=base_url)


def _get_model() -> str:
    return os.environ.get("LLM_MODEL") or _DEFAULT_MODEL


def analyze_mood(mood_input: str, client: Optional[OpenAI] = None) -> dict:
    """Use the LLM to analyze a mood description and extract search keywords.

    Returns a dict with:
    - mood: short label (e.g. 'melancholic nostalgia')
    - description: expanded 1-sentence vibe
    - search_keywords: list of music-related search terms
    - genres: suggested music genres
    """
    if client is None:
        client = _get_openai_client()

    prompt = f"""Analyze this mood description and extract music-relevant metadata.

Mood: "{mood_input}"

Respond with a JSON object:
{{
    "mood": "short mood label (2-4 words)",
    "description": "one sentence vibe description",
    "search_keywords": ["3-5 music search keywords capturing this mood"],
    "genres": ["2-3 music genres that match"]
}}

Only output the JSON, no other text."""

    response = client.chat.completions.create(
        model=_get_model(),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)


def curate_mixtape(
    mood_input: str,
    tracks: list[Track],
    client: Optional[OpenAI] = None,
) -> Mixtape:
    """Curate a mixtape from mood description and search results.

    The LLM selects the best tracks, names the playlist, and explains
    why each song fits the mood.

    Args:
        mood_input: The original mood description from the user.
        tracks: List of Track objects from MusicBrainz search.
        client: Optional OpenAI client (for injection/testing).

    Returns:
        A fully populated Mixtape object.
    """
    if client is None:
        client = _get_openai_client()

    # Build a compact list of available tracks for the LLM to choose from
    track_list = []
    for i, t in enumerate(tracks, 1):
        track_list.append(f"{i}. \"{t.title}\" by {t.artist}" + (f" (album: {t.release})" if t.release else ""))

    track_text = "\n".join(track_list[:40])  # Cap at 40 tracks

    prompt = f"""You are a world-class DJ and music curator. A user described their mood as:
"{mood_input}"

Here are real songs from MusicBrainz that somewhat match this mood:

{track_text}

Create a themed mixtape of exactly 8 songs from the list above. Choose songs that best fit the mood.

Respond with JSON only:
{{
    "playlist_name": "creative playlist name (3-6 words)",
    "cover_art_description": "detailed DALL-E prompt for the cover art (1-2 sentences, visual only)",
    "vibe_description": "one sentence describing the overall vibe of this mixtape",
    "songs": [
        {{
            "index": 1,
            "title": "exact song title from list",
            "artist": "exact artist name from list",
            "why_it_fits": "1 sentence explaining why this song matches the mood"
        }}
    ]
}}

Pick exactly 8 diverse songs that together tell an emotional story matching the mood."""

    response = client.chat.completions.create(
        model=_get_model(),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "{}"
    data = json.loads(content)

    mood_analysis = analyze_mood(mood_input, client)

    songs = []
    for s in data.get("songs", []):
        songs.append(
            MixtapeSong(
                title=s.get("title", "Unknown"),
                artist=s.get("artist", "Unknown"),
                why_it_fits=s.get("why_it_fits", ""),
            )
        )

    return Mixtape(
        mood=mood_analysis.get("mood", mood_input),
        mood_description=mood_analysis.get("description", ""),
        playlist_name=data.get("playlist_name", f"{mood_analysis.get('mood', 'Mood')} Mixtape"),
        cover_art_description=data.get("cover_art_description", ""),
        vibe_description=data.get("vibe_description", ""),
        songs=songs,
    )