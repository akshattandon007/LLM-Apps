"""LLM integration — the conversational aviation expert.

When a user taps a plane and asks "what is this aircraft?" or "how long is
this route?", we hand the flight's live data to an LLM with an aviation-nerd
system prompt and stream back a grounded answer.

Provider is pluggable via ``FOM_LLM_PROVIDER``:
  * ``anthropic`` (default) -> Claude
  * ``openai``              -> any OpenAI-compatible chat endpoint
  * ``none``                -> feature disabled (UI hides the chat box)

We deliberately call the HTTP APIs directly with httpx rather than pulling in
heavy SDKs — one fewer dependency, full control over timeouts.
"""

from __future__ import annotations

import json
import logging

import httpx

from ..config import Settings
from ..models import ChatResponse, Flight

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are the in-app aviation expert for 'Flights Over Me', a real-time "
    "overhead flight tracker. You are knowledgeable, precise and a genuine "
    "aviation enthusiast. Answer the user's question about the aircraft "
    "overhead using the flight data provided as JSON context. "
    "Explain things a curious plane-spotter would love: aircraft type and "
    "manufacturer, typical role, the route and roughly how far/long it is, "
    "what the altitude and speed imply about its phase of flight (climb, "
    "cruise, descent), and any fun facts. When the data includes a bearing "
    "and elevation angle, you can tell the user exactly where to look in the "
    "sky (e.g. 'look to the WSW, about 50° above the horizon'). If a field is "
    "missing, say so briefly rather than inventing it. Use the metric/imperial "
    "units the user uses, default to both. Keep answers tight and friendly — a "
    "short paragraph or a few bullets, not an essay."
)


class LLMError(RuntimeError):
    pass


def _flight_context(flight: Flight | None) -> str:
    if flight is None:
        return "No specific flight is selected."
    payload = {
        "callsign": flight.callsign,
        "airline": flight.airline,
        "origin_country_of_registration": flight.origin_country,
        "aircraft_type": flight.aircraft_type,
        "registration": flight.registration,
        "route": flight.route.model_dump() if flight.route else None,
        "altitude_ft": flight.altitude_ft,
        "ground_speed_kts": flight.speed_kts,
        "heading_deg": flight.true_track_deg,
        "vertical_rate_ms": flight.vertical_rate_ms,
        "on_ground": flight.on_ground,
        "ground_distance_from_observer_km": flight.distance_km,
        "bearing_from_observer_deg": flight.bearing_deg,
        "elevation_above_horizon_deg": flight.elevation_deg,
        "slant_range_km": flight.slant_range_km,
        "is_directly_overhead": flight.is_overhead,
    }
    return json.dumps(payload, indent=2)


class LLMClient:
    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self._s = settings
        self._http = client

    async def ask(self, question: str, flight: Flight | None) -> ChatResponse:
        if not self._s.llm_enabled:
            raise LLMError(
                "LLM features are disabled. Set FOM_LLM_PROVIDER and the "
                "matching API key in your environment to enable them."
            )
        user_content = (
            f"Flight data context:\n{_flight_context(flight)}\n\n"
            f"Question: {question.strip()}"
        )
        if self._s.llm_provider == "anthropic":
            return await self._ask_anthropic(user_content)
        if self._s.llm_provider == "openai":
            return await self._ask_openai(user_content)
        raise LLMError(f"Unknown LLM provider: {self._s.llm_provider}")

    async def _ask_anthropic(self, user_content: str) -> ChatResponse:
        try:
            resp = await self._http.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self._s.anthropic_api_key or "",
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self._s.llm_model,
                    "max_tokens": self._s.llm_max_tokens,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_content}],
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as exc:
            raise LLMError(f"Anthropic request failed: {exc}") from exc

        text = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        ).strip()
        return ChatResponse(answer=text, provider="anthropic", model=self._s.llm_model)

    async def _ask_openai(self, user_content: str) -> ChatResponse:
        try:
            resp = await self._http.post(
                f"{self._s.openai_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._s.openai_api_key or ''}",
                    "content-type": "application/json",
                },
                json={
                    "model": self._s.llm_model,
                    "max_tokens": self._s.llm_max_tokens,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as exc:
            raise LLMError(f"OpenAI request failed: {exc}") from exc

        text = data["choices"][0]["message"]["content"].strip()
        return ChatResponse(answer=text, provider="openai", model=self._s.llm_model)
