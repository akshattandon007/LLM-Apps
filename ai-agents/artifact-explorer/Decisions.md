# Decisions — *Why* every architectural choice was made

This document captures every decision's rationale so you (and future you) never
have to guess why something was done a certain way.

## 1. CLI over mobile app

**Decision:** Build as a Python CLI tool, not a mobile app.

**Why:** The brief says "take a photo of anything" which sounds mobile-first, but
the core value is the *narrative depth* — the object story — not the camera UX.
Building a mobile app introduces platform SDKs, build signing, app stores, and a
10× engineering surface. A Python CLI simulates the same pipeline with ~1/10 the
code, and can be wrapped into a mobile backend later once the content experience
is validated. The `--snap` flag already accepts an image path to anticipate that
upgrade path.

## 2. Simulated vision over real computer vision

**Decision:** MVP uses a keyword-matched artifact library (no real vision).

**Why:** Real image classification (CLIP, GPT-4o vision, or a custom model) adds
API costs, latency, model dependencies, and failure modes on edge cases. The
value we're testing is: *do people enjoy reading artifact stories?* Not *can we
identify objects accurately?* Simulated vision with 8+ rich presets lets us
validate the narrative experience before spending on vision infrastructure.
The `--snap` flag and `identify_from_image()` stub prepares the real path.

## 3. Artifact-as-data approach (single Pydantic model)

**Decision:** A single `Artifact` model holds all data (identification + story +
metadata). No relational schema, no DB.

**Why:** For a CLI tool with 8 presets, a database is over-engineering. A single
`BaseModel` with all fields co-located makes the data easy to test, serialise,
and extend. The `briefing_date` field (aliased as `date`) keeps it API-friendly
without clashing with the `date` stdlib import. If the artifact library grows
beyond ~100 entries, we can migrate to SQLite — but not before.

## 4. Module separation (identifier / historian / gallery)

**Decision:** Three separate modules with strict responsibilities.

**Why:** Each stage of the pipeline (identify → enrich → display) has different
failure modes and different testing strategies. Keeping them separated means:
- `identifier.py` can be swapped for a real vision client without touching the story data.
- `historian.py` can be extended with an LLM backend without changing how objects are identified.
- `gallery.py` can be swapped for HTML, JSON, or SMS output without changing the data model.
Single-responsibility modules pay off immediately in test clarity.

## 5. Pydantic aliased field for `date`

**Decision:** Field named `briefing_date` with `alias="date"`.

**Why:** `from datetime import date` imports the type `date`. A field named
`date` shadows the imported type, causing Pyright errors. Renaming the field to
`briefing_date` and using `alias="date"` keeps the serialization contract
(`{"date": "2026-08-27"}`) intact while avoiding the name clash. This is a
common Pydantic v2 pattern — documented in memory as a standing rule.

## 6. Keyword-map fuzzy matching over NLP

**Decision:** Simple `list[tuple[list[str], str]]` keyword matching.

**Why:** For 8 artifacts, a full NLP pipeline (spaCy, sentence-transformers) would
be absurd over-engineering. Keyword matching is deterministic, testable, and
obvious — each line says "if these words appear, match this artifact". It handles
partial queries ("roman coin silver"), misspellings, and multi-word descriptions
equally well. The KEYWORD_MAP pattern is trivially extensible.

## 7. Rich card output over raw JSON

**Decision:** ASCII-gallery card with emoji headers and word-wrapped sections.

**Why:** This is a storytelling tool — raw JSON or a terse table kills the
experience. The `CARD_TEMPLATE` with borders, section dividers, and bullet
points makes the output shareable via screenshot, text-forward, or paste. It
feels like a "discovery moment" rather than a data dump.