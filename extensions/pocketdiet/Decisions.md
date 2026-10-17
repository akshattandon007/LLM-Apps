# Architectural Decisions

## 1. Stdlib-only policy

**Chosen:** Use only Python stdlib (urllib, json, argparse).
**Rejected:** requests + rich + click (more ergonomic but add dependencies).
**Rationale:** The spec explicitly requires zero external deps.  Urllib + json
suffice for the single HTTP API.  Argparse is built-in and adequate for this
argument surface.  Avoids pip-install friction and lockfile maintenance.

## 2. Separate api.py module

**Chosen:** API client lives in its own module, not inlined in cli.py.
**Rejected:** Putting `urllib.request.urlopen()` calls directly in the CLI
handler.
**Rationale:** Separation of concerns.  The API module is testable in isolation,
and the CLI module never needs to import urllib directly.  Also makes it
trivial to swap to `requests` or `httpx` in a fork without touching
presentation logic.

## 3. Search vs barcode as separate code paths

**Chosen:** Two independent API functions (`search_foods`, `lookup_barcode`)
called from separate CLI handlers (`_handle_search`, `_handle_barcode`).
**Rejected:** A single unified `fetch_product(identifier)` that tries to detect
whether input is a barcode vs a name.
**Rationale:** Open Food Facts has two completely different endpoints with
different response shapes (search returns a list; barcode returns a single
product with `status: 1`).  Merging them adds heuristics (is "123" a barcode?)
that are fragile and opaque.  Explicit `--barcode` flag is clearer for the
user and simpler in code.

## 4. _fetch_json swallows all exceptions

**Chosen:** `_fetch_json()` catches `URLError`, `JSONDecodeError`, `OSError`,
`ValueError` and returns an empty dict.
**Rejected:** Letting exceptions propagate to the CLI handler for user-facing
error messages.
**Rationale:** Network calls are inherently unreliable.  The CLI should show
"No products found" rather than a raw traceback for a timeout.  The empty-dict
pattern keeps error handling uniform: callers check "did I get data?" with a
single truthy/falsy test.  Downside: silent failures on transient blips, but
acceptable for a CLI tool (retry is a user action).

## 5. Per-100 g scaling with servings

**Chosen:** Store per-100 g values in the nutriments dict, multiply by
`servings` at verdict time.
**Rejected:** Request per-serving data from the API or store a separate
per-serving dict.
**Rationale:** The OFF API returns per-100 g values reliably; per-serving
quantities are optional and inconsistent.  By storing the raw per-100 g values
and applying a multiplier at display time we get consistent behaviour and can
re-parse with different serving sizes without hitting the network again.

## 6. _100g key fallback

**Chosen:** `parse_nutriments` reads both `energy-kcal` and `energy-kcal_100g`,
then `get_serving_values` prefers `_100g` before falling back to the
unqualified key.
**Rejected:** Only reading the `_100g` keys; or only reading unqualified keys.
**Rationale:** The OFF API sometimes returns only one variant.  Supporting both
maximises compatibility without extra API calls.  The `_100g` preference is
correct because that is the normalised per-100 g value, while the unqualified
key may be per-serving (unknown serving size).

## 7. Verdict levels as three-tier system

**Chosen:** Three levels per nutrient: good / warning / bad (plus None for
neutral items).
**Rejected:** Two-tier (pass/fail) or continuous score (0-100).
**Rationale:** Three tiers match how people think about food labels (green /
amber / red).  A continuous score is more precise but requires a complex
aggregation algorithm (Nutri-Score) that is out of scope.  The None level
handles "fair protein" / "moderate calories" where the verdict is neither good
nor bad, just a statement of fact.

## 8. ANSI colour coding via raw escape codes

**Chosen:** Hardcoded `\033[9Xm` sequences, only when the terminal is available.
**Rejected:** The `colorama` library or `rich` markup.
**Rationale:** Colour codes are a 5-line dict lookup.  Adding a dependency for
ANSI wrapping is unnecessary.  The trade-off: colours won't work on Windows
without colorama's `init()`.  Acceptable for a stdlib-only tool targeting
Unix-like systems.

## 9. JSON output as a separate flag, not format detection

**Chosen:** `--json` flag to switch between human-readable verdicts and raw
product JSON.
**Rejected:** Auto-detecting output format based on whether stdout is a TTY.
**Rationale:** Explicit flag is predictable and scriptable.  Auto-detection
(piped to `jq`) is clever but violates the principle of least surprise — users
should control output format.

## 10. pyproject.toml instead of setup.py

**Chosen:** `pyproject.toml` with setuptools backend.
**Rejected:** Legacy `setup.py` with `setup()` call.
**Rationale:** `pyproject.toml` is the modern PEP 621 standard.  It declaratively
lists metadata, scripts, and build requirements.  No executable code means no
accidental side effects on import.  The spec's "setup.py or pyproject.toml"
allows either.

## 11. Top N results default to 1

**Chosen:** `--top` defaults to 1, limiting output to the most relevant product.
**Rejected:** No limit (return all) or default to 5.
**Rationale:** The OFF search endpoint returns the most relevant product first.
Showing one product keeps output concise for a quick lookup.  Power users can
increase it.  Returning all results could produce hundreds of lines for common
terms like "yogurt".

## 12. Single executable entry point (cli:main)

**Chosen:** `pocketdiet.cli:main` as the console_scripts entry point, plus
`__main__.py` for `python -m pocketdiet`.
**Rejected:** Spreading logic across multiple entry points (e.g.
`pocketdiet-search`, `pocketdiet-barcode`).
**Rationale:** A single CLI tool with subcommands/flags is the standard pattern.
The `__main__.py` is required for `python -m` to work and is a trivial
delegate to `cli.main()`.

## 13. Test module imports via sys.path manipulation

**Chosen:** `sys.path.insert(0, ...)` in test files.
**Rejected:** Relying solely on `pip install -e .` for import resolution.
**Rationale:** Tests should run immediately after cloning/creating the directory,
without a mandatory install step.  The path manipulation in `tests/__init__.py`
or conftest.py is a one-liner.  After `pip install -e .` the insert becomes a
no-op (same package found via site-packages).

## 14. Separate verdicts from presentation

**Chosen:** `generate_verdicts()` returns structured dicts; `format_verdicts()`
renders them to a string.
**Rejected:** A single function that both computes and prints.
**Rationale:** The verdict logic is unit-testable without mocking stdout.  The
structured output can be consumed by a future TUI, GUI, or HTML exporter
without touching the rules.  Separation also makes the JSON output path clean
(the verdicts are not computed at all when `--json` is used).

## 15. Empty dict / empty list as "not found"

**Chosen:** API functions return empty collections on failure; the CLI checks
falsy and prints an error message.
**Rejected:** Raising custom exceptions (e.g. `ProductNotFound`).
**Rationale:** Python exceptions are heavyweight for a lookup tool where "no
result" is a common and expected outcome.  Empty collections are naturally
falsy, so `if not products: print("Not found")` reads clearly.  Custom
exceptions would need a try/except in the CLI handler for no additional
expressiveness.