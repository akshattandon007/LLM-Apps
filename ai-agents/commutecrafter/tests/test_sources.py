"""Source parsers. Pure functions only — no network in the test suite."""

from __future__ import annotations

import pytest

from commutecrafter.models import ContentItem
from commutecrafter.sources.arxiv import parse_arxiv
from commutecrafter.sources.base import SourceError, dedupe
from commutecrafter.sources.gutenberg import (
    load_catalog,
    parse_gutenberg_text,
    rank_catalog,
    strip_boilerplate,
)
from commutecrafter.sources.hackernews import clean_html, parse_hackernews
from commutecrafter.sources.wikipedia import parse_full_extract, parse_wikipedia

WIKI_PAYLOAD = {
    "query": {
        "pages": {
            "1": {
                "pageid": 1,
                "title": "History of tea",
                "extract": " ".join(["Tea"] * 120),
            },
            "2": {"pageid": 2, "title": "Stub", "extract": "too short"},
        }
    }
}

ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2401.00001v1</id>
    <title>  A Study of
      Retrieval   Systems </title>
    <summary>{summary}</summary>
    <published>2024-01-02T10:00:00Z</published>
  </entry>
</feed>
""".format(summary=" ".join(["retrieval"] * 60))

HN_PAYLOAD = {
    "hits": [
        {
            "objectID": "123",
            "title": "Ask HN: How do you read more?",
            "story_text": "<p>I have tried " + " ".join(["many"] * 200) + "</p>",
            "created_at": "2024-05-01T00:00:00Z",
        },
        {"objectID": "456", "title": "A link post", "story_text": "", "url": "https://example.com"},
    ]
}

GUTENBERG_TEXT = """The Project Gutenberg eBook of Meditations

*** START OF THE PROJECT GUTENBERG EBOOK MEDITATIONS ***

{body}

*** END OF THE PROJECT GUTENBERG EBOOK MEDITATIONS ***
license boilerplate that should never be counted
""".format(body=" ".join(["word"] * 500))


def test_parse_wikipedia_extracts_items():
    items = parse_wikipedia(WIKI_PAYLOAD)
    assert len(items) == 1
    assert items[0].title == "History of tea"
    assert items[0].source == "wikipedia"
    assert items[0].words == 120
    assert items[0].url.endswith("History_of_tea")


def test_parse_wikipedia_rejects_bad_payload():
    with pytest.raises(SourceError):
        parse_wikipedia({"query": {"pages": ["nope"]}})


def test_parse_full_extract_counts_words():
    payload = {"query": {"pages": {"7": {"title": "X", "extract": " ".join(["a"] * 4321)}}}}
    words, excerpt = parse_full_extract(payload)
    assert words == 4321
    assert excerpt.startswith("a a")


def test_parse_full_extract_missing_page():
    assert parse_full_extract({"query": {"pages": {"-1": {"missing": ""}}}}) == (0, "")


def test_parse_arxiv_normalises_title_and_url():
    items = parse_arxiv(ARXIV_XML)
    assert len(items) == 1
    assert items[0].title == "A Study of Retrieval Systems"
    assert items[0].url.startswith("https://arxiv.org/abs/2401.00001")
    assert items[0].published == "2024-01-02"
    assert items[0].category == "deep"


def test_parse_arxiv_bad_xml():
    with pytest.raises(SourceError):
        parse_arxiv("<not-xml")


def test_parse_hackernews_keeps_only_text_posts():
    items = parse_hackernews(HN_PAYLOAD)
    assert len(items) == 1
    assert items[0].url == "https://news.ycombinator.com/item?id=123"
    assert items[0].words >= 200
    assert items[0].category == "news"


def test_clean_html_strips_tags_and_entities():
    assert clean_html("<p>Hello &amp; goodbye</p>") == "Hello & goodbye"


def test_strip_boilerplate():
    body = strip_boilerplate(GUTENBERG_TEXT)
    assert "START OF THE PROJECT" not in body
    assert "END OF THE PROJECT" not in body
    assert "license boilerplate" not in body


def test_parse_gutenberg_text_caps_words():
    words, excerpt = parse_gutenberg_text(GUTENBERG_TEXT, limit_words=200)
    assert words == 200
    assert excerpt.startswith("word word")


def test_parse_gutenberg_empty():
    assert parse_gutenberg_text("", limit_words=100) == (0, "")


def test_catalog_loads_and_is_not_empty():
    catalog = load_catalog()
    assert len(catalog) >= 10
    assert all({"id", "title", "tags"} <= set(entry) for entry in catalog)


def test_rank_catalog_prefers_tag_matches():
    catalog = [
        {"id": 1, "title": "Cookery", "tags": ["food"]},
        {"id": 2, "title": "Stoic Letters", "tags": ["philosophy", "stoicism"]},
    ]
    ranked = rank_catalog(catalog, "philosophy")
    assert ranked[0]["id"] == 2


def test_rank_catalog_is_stable_without_matches():
    catalog = [{"id": 1, "title": "A", "tags": []}, {"id": 2, "title": "B", "tags": []}]
    assert [e["id"] for e in rank_catalog(catalog, "zzz")] == [1, 2]


def test_dedupe_drops_repeat_url_and_title():
    items = [
        ContentItem("Same", "wikipedia", "http://x/1", 100),
        ContentItem("Same", "arxiv", "http://x/2", 100),
        ContentItem("Other", "wikipedia", "HTTP://X/1", 100),
        ContentItem("Kept", "arxiv", "http://x/3", 100),
    ]
    out = dedupe(items)
    assert [i.title for i in out] == ["Same", "Kept"]


class TestSourceRegistry:
    def test_build_sources_all(self):
        from commutecrafter.sources import SOURCE_NAMES, build_sources

        sources = build_sources()
        assert [s.name for s in sources] == list(SOURCE_NAMES)

    def test_build_sources_subset(self):
        from commutecrafter.sources import build_sources

        assert [s.name for s in build_sources(["wikipedia"])] == ["wikipedia"]

    def test_build_sources_unknown_raises(self):
        from commutecrafter.sources import build_sources

        with pytest.raises(ValueError):
            build_sources(["myspace"])
