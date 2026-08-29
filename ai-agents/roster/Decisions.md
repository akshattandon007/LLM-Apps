# Decisions — Roster

**Why every architectural choice was made, not just what was chosen.**

---

## CLI over web

**Decision:** CLI tool, not a web app or API.

**Why:** This is a thin v1 that needs to ship fast. A CLI has zero deployment
surface — no server, no frontend, no auth, no rate limits, no uptime SLO. The
user runs `python main.py --simulate` and it works. A web version would be the
natural v2 if the product proves sticky, but the CLI lets us validate the roast
engine and tone definitions without infrastructure overhead.

**Trade-off accepted:** No shareable URL out of the box. The roast card output
is plain text that users copy-paste to groups, save as a file, or screenshot.
Adding a share endpoint (a static HTML card generator) would be a thin addition
on top of the existing `format_card` function.

---

## Tone as data, not logic

**Decision:** Tone definitions are Pydantic model instances in `tones.py`, not
inheritance hierarchies or strategy pattern classes.

**Why:** Tones are configuration, not behaviour. Each tone has a name,
description, vibe, example phrases, and intensity — all data fields. There is
no behavioural method that differs between tones (the roast templates are
selected by tone name in a dict). If we made each tone a class we'd end up with
dead code and a factory just to select one. Data-driven is simpler to extend
and test.

**Trade-off accepted:** Adding a new tone means adding a data object and a dict
entry — no new class, no new import — but the simulated roast templates for
that tone must also be added to `roaster.py`'s `_SIMULATED_ROASTS` dict. If the
number of tones grows past ~20, extracting templates into per-tone YAML or JSON
files might be cleaner.

---

## Simulated roasts with a live LLM placeholder

**Decision:** v1 ships with preset template roasts (simulated mode). The
`Roaster` class has a `set_client()` injection method and a `_live_roast()`
placeholder for future LLM integration.

**Why:** A real LLM call requires an API key, a provider, error handling, prompt
engineering, response parsing, and cost management. That's a separate build
cycle. The simulated mode proves the data model, the tone system, and the card
format — the hard parts — without any external dependency. Users can immediately
run `--simulate` or `--roast` and get results. The `set_client()` pattern
mirrors how we've done it in other projects (AlphaBrief, PR Auto-Pilot) so
adding LLM support later slots in cleanly.

**Trade-off accepted:** Simulated roasts are repetitive after the second run.
They pull from a fixed pool of templates per tone. This is acceptable for a v1
that demonstrates the concept. Real LLM roasting will generate unique, context-
aware burns by consuming the person's description, expression, outfit, vibe,
body language, and arrangement — the templates just show the structure.

---

## Module separation

**Decision:** Four modules under `src/` plus a `main.py` entry point.

**Why:** Each concern maps to a file:
- `models.py` — the data shapes (Person, Roast, Tone, RoastCard, etc.). Single
  source of truth for what a roast *is*.
- `tones.py` — tone definitions. Pure data, isolated from generation logic.
- `roaster.py` — the engine. Takes models in, produces models out.
- `card.py` — formatting. Takes models, produces display text.
- `main.py` — CLI wiring. Thin glue, no business logic.

This lets us test modules independently (e.g. test tones without importing
roaster, test card formatting without generating roasts).

**Trade-off accepted:** Four files instead of one big one. Worth it for test
isolation.

---

## pydantic for models (not dataclasses)

**Decision:** pydantic v2 instead of stdlib dataclasses.

**Why:** Pydantic gives us field validation (intensity between 1-10, enums with
proper string handling), serialisation to dict/JSON for future API use, and a
consistent pattern across projects (see AlphaBrief, HomeCourt). Dataclasses
would work but we'd need to add validation manually.

**Trade-off accepted:** pydantic is a dependency. It's already in our standard
stack (used in AlphaBrief, PR Auto-Pilot, etc.), so no net new cost.

---

## Simulated-only tests (no mocks of LLM)

**Decision:** All tests use `simulate=True`. No API calls, no mocking of an LLM.

**Why:** We don't have a live LLM implementation yet. The tests validate that
the data pipeline works: tone → group → roasts → card. That's the important
part. When live LLM support is added, we'll add integration tests with
`set_client()` injecting a test key.

**Trade-off accepted:** Tests don't exercise the live path. That path currently
falls back to simulated anyway, so testing it would just test the fallback.

---

## Python 3.10+ features

**Decision:** `from __future__ import annotations`, type hints, `list[str]`
syntax.

**Why:** The VPS runs Python 3.11+. Using `from __future__` avoids import-time
evaluation of annotations. Modern type syntax is clearer.

**Trade-off accepted:** None — Python 3.10+ is the baseline.

---

## No image processing in v1

**Decision:** The user describes the photo. No actual image input, no Pillow
image analysis.

**Why:** Real image analysis (facial expression detection, pose estimation,
outfit classification) is an entirely separate domain requiring ML models or an
API. That's a v2 feature. v1 asks "describe the people" and roasts what you
tell it.

**Trade-off accepted:** The user has to describe their own photo. The quality of
the roast depends on the quality of the description. A real photo upload +
analysis mode would be the obvious v2 improvement.

---

## Card output as plain text (not image / PNG)

**Decision:** The roast card is a plain-text block with box-drawing characters
and emoji, printable to terminal or saved as `.txt`.

**Why:** An image card (styled PNG like a greeting card) requires Pillow or a
rendering library. That's a separate build. Plain text works everywhere —
terminal, copy-paste to messages, save to file. The box-drawing and emoji give
it visual structure without a rendering dependency.

**Trade-off accepted:** No visual card image. The text is functional but won't
look as polished as a designed card. If the product gains traction, generating
a shareable PNG via Pillow (already in requirements.txt for future use) or an
HTML-based card would be the natural upgrade.