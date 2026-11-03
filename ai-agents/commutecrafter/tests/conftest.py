"""Shared fixtures. No test may touch the network or the real user cache."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

PKG_DIR = Path(__file__).resolve().parents[1] / "commutecrafter"
CORPUS = PKG_DIR / "data" / "sample_corpus.json"


@pytest.fixture(autouse=True)
def isolated_env(tmp_path, monkeypatch):
    """Point the store at a temp DB and blank out any real API keys."""
    monkeypatch.setenv("COMMUTECRAFTER_DB", str(tmp_path / "test.db"))
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    yield


@pytest.fixture(scope="session")
def corpus_records() -> list[dict]:
    with open(CORPUS, "r", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture()
def corpus_items(corpus_records):
    from commutecrafter.models import ContentItem

    return [
        ContentItem(
            title=rec["title"],
            source=rec["source"],
            url=rec["url"],
            words=rec["words"],
            summary=rec.get("summary", ""),
            category=rec.get("category", "general"),
        )
        for rec in corpus_records
    ]
