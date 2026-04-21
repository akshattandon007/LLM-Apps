"""
tests/test_agent.py
Unit tests for BartenderAI helper functions.
Run with:  pytest tests/
"""

from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agent import (
    get_season,
    extract_text,
    parse_json,
    get_location,
    get_weather,
    get_trending_cocktails,
    make_my_cocktail,
)


# ── get_season ─────────────────────────────────────────────────────────────

class TestGetSeason:
    def _mock_month(self, month: int):
        with patch("agent.datetime") as mock_dt:
            mock_dt.now.return_value.month = month
            return get_season()

    def test_winter_december(self):
        assert self._mock_month(12) == "Winter"

    def test_winter_january(self):
        assert self._mock_month(1) == "Winter"

    def test_spring_april(self):
        assert self._mock_month(4) == "Spring"

    def test_summer_july(self):
        assert self._mock_month(7) == "Summer"

    def test_autumn_october(self):
        assert self._mock_month(10) == "Autumn"


# ── extract_text ──────────────────────────────────────────────────────────

class TestExtractText:
    def _make_response(self, blocks):
        resp = MagicMock()
        resp.content = [
            MagicMock(type=b["type"], text=b.get("text", "")) for b in blocks
        ]
        return resp

    def test_single_text_block(self):
        resp = self._make_response([{"type": "text", "text": '{"key": "value"}'}])
        assert extract_text(resp) == '{"key": "value"}'

    def test_strips_json_fence(self):
        resp = self._make_response([{"type": "text", "text": "```json\n[1,2,3]\n```"}])
        assert extract_text(resp) == "[1,2,3]"

    def test_skips_non_text_blocks(self):
        resp = self._make_response([
            {"type": "tool_use"},
            {"type": "text", "text": "hello"},
        ])
        assert extract_text(resp) == "hello"

    def test_empty_response(self):
        resp = self._make_response([])
        assert extract_text(resp) == ""


# ── parse_json ────────────────────────────────────────────────────────────

class TestParseJson:
    def test_valid_list(self):
        assert parse_json('[{"a": 1}]') == [{"a": 1}]

    def test_valid_dict(self):
        assert parse_json('{"name": "Negroni"}') == {"name": "Negroni"}

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="valid JSON"):
            parse_json("not json at all")


# ── get_location ──────────────────────────────────────────────────────────

class TestGetLocation:
    def test_success(self):
        fake = {"status": "success", "city": "Paris", "country": "France",
                "lat": 48.85, "lon": 2.35}
        with patch("agent.httpx.get") as mock_get:
            mock_get.return_value.json.return_value = fake
            loc = get_location()
        assert loc["city"] == "Paris"
        assert loc["country"] == "France"
        assert loc["lat"] == 48.85

    def test_fallback_on_failure(self):
        with patch("agent.httpx.get", side_effect=Exception("network")):
            loc = get_location()
        assert loc["city"] == "London"
        assert loc["lat"] == 51.5


# ── get_weather ───────────────────────────────────────────────────────────

class TestGetWeather:
    def test_clear_sky(self):
        payload = {"current_weather": {"weathercode": 0, "temperature": 22.4}}
        with patch("agent.httpx.get") as mock_get:
            mock_get.return_value.json.return_value = payload
            w = get_weather(51.5, -0.12)
        assert w["temp"] == 22
        assert w["desc"] == "Clear sky"
        assert w["unit"] == "°C"

    def test_rainy(self):
        payload = {"current_weather": {"weathercode": 61, "temperature": 10.0}}
        with patch("agent.httpx.get") as mock_get:
            mock_get.return_value.json.return_value = payload
            w = get_weather(51.5, -0.12)
        assert w["desc"] == "Light rain"

    def test_fallback_on_error(self):
        with patch("agent.httpx.get", side_effect=Exception("timeout")):
            w = get_weather(0, 0)
        assert w["temp"] == 15
        assert w["desc"] == "Mild"


# ── get_trending_cocktails ────────────────────────────────────────────────

class TestGetTrendingCocktails:
    SAMPLE = [
        {
            "rank": 1, "name": "Aperol Spritz", "badge": "trending",
            "description": "Perfect for warm evenings.", "socialBuzz": "Viral on TikTok",
            "sources": ["tiktok", "youtube"],
            "ingredients": ["90ml Prosecco", "60ml Aperol", "splash of soda"],
            "steps": ["Fill glass with ice.", "Pour Aperol.", "Top with Prosecco."],
            "bartenderTip": "Use chilled Prosecco.",
        }
    ]

    def _mock_client(self):
        client = MagicMock()
        resp   = MagicMock()
        resp.content = [MagicMock(type="text", text=json.dumps(self.SAMPLE))]
        client.messages.create.return_value = resp
        return client

    def test_returns_list(self):
        loc    = {"city": "London", "country": "UK", "lat": 51.5, "lon": -0.12}
        weather = {"temp": 20, "desc": "Clear", "unit": "°C"}
        result  = get_trending_cocktails(self._mock_client(), loc, weather, "Summer")
        assert isinstance(result, list)
        assert result[0]["name"] == "Aperol Spritz"

    def test_web_search_tool_is_passed(self):
        client  = self._mock_client()
        loc     = {"city": "London", "country": "UK", "lat": 51.5, "lon": -0.12}
        weather = {"temp": 20, "desc": "Clear", "unit": "°C"}
        get_trending_cocktails(client, loc, weather, "Summer")
        call_kwargs = client.messages.create.call_args[1]
        assert any(t.get("type") == "web_search_20250305"
                   for t in call_kwargs.get("tools", []))


# ── make_my_cocktail ──────────────────────────────────────────────────────

class TestMakeMycocktail:
    SAMPLE = {
        "name": "Gin & Tonic", "tagline": "A British classic.",
        "description": "Crisp and refreshing.", "trendingNote": "Always popular.",
        "usedIngredients": ["gin", "tonic water"],
        "additionalIngredients": ["lime"],
        "ingredients": ["50ml gin", "150ml tonic water", "lime wedge"],
        "steps": ["Fill glass with ice.", "Pour gin.", "Top with tonic.", "Garnish."],
        "bartenderTip": "Use premium tonic.",
        "source": "IBA classic",
    }

    def _mock_client(self):
        client = MagicMock()
        resp   = MagicMock()
        resp.content = [MagicMock(type="text", text=json.dumps(self.SAMPLE))]
        client.messages.create.return_value = resp
        return client

    def test_returns_dict(self):
        result = make_my_cocktail(self._mock_client(), ["gin", "tonic water"])
        assert isinstance(result, dict)
        assert result["name"] == "Gin & Tonic"

    def test_ingredients_in_prompt(self):
        client = self._mock_client()
        make_my_cocktail(client, ["gin", "lime juice", "sugar syrup"])
        call_kwargs = client.messages.create.call_args[1]
        user_content = call_kwargs["messages"][0]["content"]
        assert "gin" in user_content
        assert "lime juice" in user_content
