# Decisions.md — SpillBuddy

## 1. CLI-first over Web App
- **Chosen:** CLI tool (argparse)
- **Rejected:** Web app (Flask/Streamlit) or GUI
- **Why:** Extensions category demands CLI tools. Faster to build, no server required, works offline. Users can pipe output, script it, or use it in automated workflows.

## 2. Local database over API
- **Chosen:** Hardcoded Python dictionary (STAIN_DB)
- **Rejected:** External API (wikihow, cleaning product APIs) or SQLite database
- **Why:** No API key needed, works offline, instant response. A dictionary is easy to extend and maintain. SQLite would be overkill for a read-only lookup table with ~100 entries.

## 3. Dictionary-of-dictionaries over flat file (CSV/JSON)
- **Chosen:** Nested Python dict: `stain → fabric → (method, caution)`
- **Rejected:** CSV file, JSON file, YAML file
- **Why:** Directly importable, no file I/O overhead, type-safe, easy to extend inline. JSON/CSV would need parsing and wouldn't be as maintainable inline.

## 4. Separate data and CLI modules over monolith
- **Chosen:** `data.py` (data + lookup functions) + `cli.py` (argparse + output)
- **Rejected:** Single `spillbuddy.py` file
- **Why:** Separation of concerns — data can be tested independently. CLI changes don't affect the database. Future UI (TUI, web) can reuse data.py without touching CLI code.

## 5. "all" fabric fallback over strict fabric matching
- **Chosen:** Each stain has a fallback `"all"` entry used when the requested fabric isn't in the stain's specific list
- **Rejected:** Requiring exact fabric match for every stain, or returning an error for unknown fabrics
- **Why:** Users won't know the exact fabric name. A fallback gives a reasonable generic method rather than "stain not found." Better UX.

## 6. Subcommands (lookup/list/interactive) over flags
- **Chosen:** `spillbuddy lookup <stain> <fabric>`, `spillbuddy list`, `spillbuddy interactive`
- **Rejected:** Flags like `spillbuddy --stain "red wine" --fabric cotton`
- **Why:** Subcommands are more discoverable, extensible (add `search`, `export` later), and follow CLI conventions (git, pip, etc.).

## 7. Interactive mode as a subcommand over `spillbuddy` with no args
- **Chosen:** Explicit `spillbuddy interactive` subcommand
- **Rejected:** Launching interactive mode when no args are given
- **Why:** Running a command with no args should show help, not start a potentially long session. Users who want interactive mode opt in explicitly.

## 8. Human-readable caution text over codes
- **Chosen:** Full-sentence caution text per entry
- **Rejected:** Error codes, numbered warnings, or icons
- **Why:** Readability. Users need to know "don't use hot water on blood stains" — not reference code W-103. Full text is actionable immediately.

## 9. Case-insensitive matching over exact match
- **Chosen:** `.strip().lower()` normalization on input
- **Rejected:** Case-sensitive exact match
- **Why:** Users type "Red Wine", "red wine", "RED WINE" — all should work. Lower normalization is the simplest approach.

## 10. No external dependencies over fpdf2/rich/etc.
- **Chosen:** Python stdlib only (argparse, sys)
- **Rejected:** fpdf2 (PDF export), rich (fancy terminal output), colorama
- **Why:** Zero-install for the user. `pip install -e .` gives you everything. Rich formatting would be nice but adds a dependency. PDF export can be added as a v2 feature.

## 11. pytest over unittest
- **Chosen:** pytest
- **Rejected:** unittest, doctest
- **Why:** Less boilerplate, better assertion introspection, fixtures. Industry standard for Python testing.

## 12. setup.py + pyproject.toml over just pyproject.toml
- **Chosen:** Both setup.py (for console_scripts) and pyproject.toml (for pytest config)
- **Rejected:** pyproject.toml only (PEP 621)
- **Why:** setup.py `entry_points` for `console_scripts` is the most reliable way to create the `spillbuddy` command. pyproject.toml handles test configuration cleanly.

## 13. 12 stain types initially over comprehensive database
- **Chosen:** 12 most common household stains (red wine, coffee, blood, grass, grease, ink, tomato, mud, wax, marker, sweat, chocolate) + berry, white wine, pet stains
- **Rejected:** 50+ stain types with rare ones (asphalt, tar, glue, etc.)
- **Why:** Ship the 80/20 — the stains people actually encounter. Database is trivially extensible. Adding obscure stains later has zero architectural cost.

## 14. Blot/scrape/rinse methodology over product recommendations
- **Chosen:** Home remedies (salt, vinegar, baking soda, dish soap, rubbing alcohol)
- **Rejected:** Commercial product recommendations (Shout, OxiClean, specific brands)
- **Why:** Home remedies work immediately with what you have in the kitchen. Brand recommendations go out of date and vary by region. Products can be a future "advanced" mode.