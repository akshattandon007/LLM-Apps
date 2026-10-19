"""Tests for the LLM voice layer + template fallback (offline, hermetic)."""

import json

import pytest

from thenpaper import voice
from thenpaper.api import DayFacts, DayItem


def make_facts() -> DayFacts:
    return DayFacts(
        month=10,
        day=19,
        events=[DayItem(year=1969, text="Apollo 11 splashdown celebration", kind="event")],
        births=[DayItem(year=1990, text="A future coder, born this day", kind="birth")],
        deaths=[],
        holidays=[],
        selected=[],
        source="live",
    )


def test_templates_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    enh = voice.enhance(make_facts(), 10, 19, allow_llm=True)
    assert not enh.used_llm
    assert enh.headline
    assert enh.dek
    assert enh.twin_intro
    assert "1969" in enh.headline


def test_allow_llm_false_uses_templates(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")
    enh = voice.enhance(make_facts(), 10, 19, allow_llm=False)
    assert not enh.used_llm


def test_llm_success_anthropic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")

    def fake_poster(url: str, headers: dict, payload: dict) -> str:
        assert url == voice.ANTHROPIC_URL
        assert headers["x-api-key"] == "sk-ant-fake"
        assert payload["messages"][0]["role"] == "user"
        return json.dumps(
            {"content": [{"type": "text", "text": json.dumps(
                {"headline": "MOON WALKS SHOCK THE WORLD",
                 "dek": "A giant leap for all of us.",
                 "twin_intro": "Your birthday twins are born today."}
            )}]}
        )

    voice.set_poster(fake_poster)
    enh = voice.enhance(make_facts(), 10, 19)
    assert enh.used_llm
    assert enh.headline == "MOON WALKS SHOCK THE WORLD"
    assert enh.dek == "A giant leap for all of us."
    assert enh.twin_intro == "Your birthday twins are born today."


def test_llm_success_openai(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")

    def fake_poster(url: str, headers: dict, payload: dict) -> str:
        assert url == voice.OPENAI_URL
        assert headers["Authorization"] == "Bearer sk-fake"
        return json.dumps(
            {"choices": [{"message": {"content": json.dumps(
                {"headline": "OPENAI HEADLINE", "dek": "Dek.", "twin_intro": "Twins."}
            )}}]}
        )

    voice.set_poster(fake_poster)
    enh = voice.enhance(make_facts(), 10, 19)
    assert enh.used_llm
    assert enh.headline == "OPENAI HEADLINE"


def test_llm_failure_falls_back_to_templates(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-fake")

    def broken_poster(url: str, headers: dict, payload: dict) -> str:
        raise ConnectionError("model down")

    voice.set_poster(broken_poster)
    enh = voice.enhance(make_facts(), 10, 19)
    assert not enh.used_llm
    assert enh.headline


def test_llm_bad_json_falls_back(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")

    def junk_poster(url: str, headers: dict, payload: dict) -> str:
        return "not json at all"

    voice.set_poster(junk_poster)
    enh = voice.enhance(make_facts(), 10, 19)
    assert not enh.used_llm


def test_parse_llm_json_tolerates_fences():
    assert voice._parse_llm_json('```json\n{"headline": "A"}\n```') == {"headline": "A"}
    assert voice._parse_llm_json('Here you go: {"headline": "B"} thanks') == {"headline": "B"}
    assert voice._parse_llm_json("garbage") == {}


def test_digest_includes_facts():
    digest = voice._digest(make_facts())
    assert "Apollo" in digest
    assert "EVENTS" in digest