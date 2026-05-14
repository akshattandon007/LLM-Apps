"""
Core mood agent — orchestrates the Claude tool-use reasoning loop.

Works without Spotify audio features (restricted endpoint) by relying on
track names, artists, genres, popularity, timestamps, and Claude's knowledge.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Callable, Optional

import anthropic

from src.agent.prompts import SYSTEM_PROMPT, build_analysis_prompt
from src.agent.tools import TOOL_DEFINITIONS, ToolExecutor
from src.spotify.models import MoodReport, RecentlyPlayedSession

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-20250514"
MAX_ITERATIONS = 12


class MoodAgent:
    def __init__(
        self,
        api_key: Optional[str] = None,
        verbose: bool = False,
        on_tool_call: Optional[Callable[[str, dict], None]] = None,
    ) -> None:
        self._client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self._verbose = verbose
        self._on_tool_call = on_tool_call

    def analyse(self, session: RecentlyPlayedSession) -> MoodReport:
        if session.track_count == 0:
            raise ValueError("Session has no tracks.")

        executor = ToolExecutor(session)

        duration = (
            f"{session.time_span_hours:.1f} hours"
            if session.time_span_hours
            else f"{session.track_count} tracks"
        )
        initial_prompt = build_analysis_prompt(
            track_list_summary=f"{session.track_count} tracks",
            session_duration=duration,
        )

        messages: list[dict[str, Any]] = [{"role": "user", "content": initial_prompt}]
        iterations = 0

        while iterations < MAX_ITERATIONS:
            iterations += 1
            if self._verbose:
                logger.info(f"Agent iteration {iterations}")

            response = self._client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )

            if self._verbose:
                logger.info(f"Stop reason: {response.stop_reason}")

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                break

            tool_results = []
            has_tool_use = False

            for block in response.content:
                if block.type != "tool_use":
                    continue
                has_tool_use = True
                tool_name = block.name
                tool_input = block.input or {}

                if self._verbose:
                    logger.info(f"Tool call: {tool_name}")
                if self._on_tool_call:
                    self._on_tool_call(tool_name, tool_input)

                result_str = executor.execute(tool_name, tool_input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_str,
                })

                if tool_name == "synthesise_mood" and executor.final_result:
                    messages.append({"role": "user", "content": tool_results})
                    break

            if not has_tool_use:
                break

            if executor.final_result is not None:
                break

            if tool_results:
                messages.append({"role": "user", "content": tool_results})

        if executor.final_result is None:
            raise RuntimeError("Agent did not produce a mood synthesis.")

        return self._build_report(executor.final_result, session)

    def _build_report(self, raw: dict[str, Any], session: RecentlyPlayedSession) -> MoodReport:
        return MoodReport(
            primary_mood=raw.get("primary_mood", "Unknown"),
            confidence=float(raw.get("confidence", 0.5)),
            energy_level=float(raw.get("energy_level", 5.0)),
            emotional_arc=raw.get("emotional_arc", "stable"),
            arc_direction=raw.get("arc_direction", "stable"),
            avg_valence=float(raw.get("avg_valence", 0.5)),
            avg_energy=float(raw.get("avg_energy", 0.5)),
            avg_danceability=float(raw.get("avg_danceability", 0.5)),
            avg_acousticness=float(raw.get("avg_acousticness", 0.5)),
            avg_instrumentalness=float(raw.get("avg_instrumentalness", 0.1)),
            avg_tempo=float(raw.get("avg_tempo", 120.0)),
            top_genres=raw.get("top_genres", []),
            dominant_mode=raw.get("dominant_mode", "major"),
            insight=raw.get("insight", ""),
            recommendations=raw.get("recommendations", []),
            tracks_analysed=session.track_count,
            session_duration_hours=session.time_span_hours,
        )
