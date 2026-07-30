"""
Tool definitions for the Claude mood analysis agent.
Works without Spotify audio features (restricted Nov 2024).
Claude uses its knowledge of artists/songs + genre/metadata signals instead.
"""

from __future__ import annotations

import json
from typing import Any

from src.spotify.models import RecentlyPlayedSession, Track

TOOL_DEFINITIONS = [
    {
        "name": "get_track_list",
        "description": (
            "Returns the recently played tracks with metadata: track name, artist, "
            "album, release year, popularity score (0-100), explicit flag, played_at timestamp, "
            "and artist genres. This is your primary data source — use Claude's knowledge of "
            "these songs and artists to infer their emotional character."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max tracks to return (default: all)",
                    "default": 50,
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_genre_analysis",
        "description": (
            "Returns a breakdown of genres listened to, with play counts. "
            "Genres are powerful mood signals — lo-fi/ambient = introspective/calm, "
            "pop/dance = upbeat/social, sad indie/emo = melancholic, metal = intense, etc."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_listening_patterns",
        "description": (
            "Returns temporal patterns: time of day listened, listening density, "
            "repeat plays, popularity spread. Useful for context — late night listening "
            "often signals introspection; high repeats signal emotional fixation."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_artist_summary",
        "description": (
            "Returns unique artists played with their genres and popularity. "
            "Artist diversity indicates mood-seeking behaviour vs comfort-seeking."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "synthesise_mood",
        "description": (
            "Call this LAST after using the other tools. "
            "Provide your final mood analysis as a JSON object."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "mood_json": {
                    "type": "string",
                    "description": "JSON string with the full mood analysis.",
                }
            },
            "required": ["mood_json"],
        },
    },
]

GENRE_EMOTIONAL_MAP: dict[str, str] = {
    "lo-fi": "calm, introspective, nostalgic",
    "ambient": "peaceful, meditative, withdrawn",
    "indie folk": "contemplative, emotional, sincere",
    "folk": "grounded, reflective, authentic",
    "bedroom pop": "vulnerable, intimate, melancholic",
    "sad indie": "melancholic, longing, cathartic",
    "emo": "intense emotion, raw vulnerability",
    "pop": "upbeat, social, optimistic",
    "dance pop": "energetic, joyful, celebratory",
    "hip hop": "confident, assertive, rhythmic",
    "rap": "confident, expressive, energetic",
    "trap": "intense, numb, detached",
    "r&b": "sensual, emotional, romantic",
    "soul": "deep emotion, warmth, authentic",
    "classical": "sophisticated, calm, focused",
    "jazz": "relaxed, sophisticated, spontaneous",
    "metal": "aggressive, cathartic, intense",
    "punk": "rebellious, frustrated, energetic",
    "country": "nostalgic, sentimental, grounded",
    "electronic": "detached, cerebral, energetic",
    "alternative": "edgy, introspective, non-conformist",
    "indie": "introspective, creative, authentic",
    "shoegaze": "dreamy, melancholic, immersive",
    "post-rock": "expansive, emotional, cinematic",
    "k-pop": "energetic, polished, upbeat",
}


class ToolExecutor:
    def __init__(self, session: RecentlyPlayedSession) -> None:
        self._session = session
        self._final_result: dict[str, Any] | None = None

    @property
    def final_result(self) -> dict[str, Any] | None:
        return self._final_result

    def execute(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        dispatch = {
            "get_track_list": self._get_track_list,
            "get_genre_analysis": self._get_genre_analysis,
            "get_listening_patterns": self._get_listening_patterns,
            "get_artist_summary": self._get_artist_summary,
            "synthesise_mood": self._synthesise_mood,
        }
        handler = dispatch.get(tool_name)
        if not handler:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        try:
            return json.dumps(handler(**tool_input), default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _get_track_list(self, limit: int = 50) -> list[dict]:
        tracks = self._session.tracks[:limit]
        return [
            {
                "position": i + 1,
                "name": t.name,
                "artist": t.primary_artist,
                "album": t.album_name,
                "release_year": t.album_release_year,
                "popularity": t.popularity,
                "explicit": t.explicit,
                "played_at": t.played_at.isoformat() if t.played_at else None,
                "genres": t.all_genres[:5],
            }
            for i, t in enumerate(tracks)
        ]

    def _get_genre_analysis(self) -> dict:
        genre_counts: dict[str, int] = {}
        for track in self._session.tracks:
            for genre in track.all_genres:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1

        sorted_genres = sorted(genre_counts.items(), key=lambda x: -x[1])[:15]
        enriched = []
        for genre, count in sorted_genres:
            emotion = "unknown"
            for key, val in GENRE_EMOTIONAL_MAP.items():
                if key.lower() in genre.lower() or genre.lower() in key.lower():
                    emotion = val
                    break
            enriched.append({
                "genre": genre,
                "track_count": count,
                "emotional_association": emotion,
            })

        return {
            "genre_breakdown": enriched,
            "total_unique_genres": len(genre_counts),
        }

    def _get_listening_patterns(self) -> dict:
        tracks = self._session.tracks
        timestamps = [t.played_at for t in tracks if t.played_at]

        # Time of day distribution
        hour_counts: dict[str, int] = {"morning (6-12)": 0, "afternoon (12-18)": 0,
                                        "evening (18-22)": 0, "night (22-6)": 0}
        for ts in timestamps:
            h = ts.hour
            if 6 <= h < 12:
                hour_counts["morning (6-12)"] += 1
            elif 12 <= h < 18:
                hour_counts["afternoon (12-18)"] += 1
            elif 18 <= h < 22:
                hour_counts["evening (18-22)"] += 1
            else:
                hour_counts["night (22-6)"] += 1

        # Repeat tracks
        track_counts: dict[str, int] = {}
        for t in tracks:
            track_counts[t.display_name] = track_counts.get(t.display_name, 0) + 1
        repeats = {k: v for k, v in track_counts.items() if v > 1}

        # Popularity spread
        pops = [t.popularity for t in tracks if t.popularity > 0]
        avg_pop = sum(pops) / len(pops) if pops else 0

        return {
            "time_of_day_distribution": hour_counts,
            "repeat_tracks": repeats,
            "avg_track_popularity": round(avg_pop, 1),
            "total_tracks": len(tracks),
            "has_timestamp_data": len(timestamps) > 0,
        }

    def _get_artist_summary(self) -> dict:
        artist_map: dict[str, dict] = {}
        for track in self._session.tracks:
            for artist in track.artists:
                if artist.name not in artist_map:
                    artist_map[artist.name] = {
                        "play_count": 0,
                        "genres": artist.genres[:4],
                        "popularity": artist.popularity,
                    }
                artist_map[artist.name]["play_count"] += 1

        sorted_artists = sorted(artist_map.items(), key=lambda x: -x[1]["play_count"])
        return {
            "artists": [{"name": n, **d} for n, d in sorted_artists[:15]],
            "unique_artist_count": len(artist_map),
            "artist_diversity": "high" if len(artist_map) > len(self._session.tracks) * 0.6 else "low",
        }

    def _synthesise_mood(self, mood_json: str) -> dict:
        try:
            result = json.loads(mood_json)
            self._final_result = result
            return {"status": "accepted", "mood": result.get("primary_mood", "unknown")}
        except json.JSONDecodeError as e:
            return {"status": "error", "message": f"Invalid JSON: {e}"}
