# Decisions.md — Renamer

## 1. CLI tool vs. GUI web app
- **Chosen:** CLI using `argparse`
- **Rejected:** Flask web UI, Tkinter desktop app
- **Why:** Extensions category targets terminal-native utilities. A CLI is faster to build, has zero dependencies, and is the right interface for a batch file renaming tool that operators script and chain.

## 2. Single file vs. package structure
- **Chosen:** Package with `renamer/__init__.py`, `renamer/core.py`, `renamer/cli.py`
- **Rejected:** Monolithic `renamer.py`
- **Why:** Separates CLI argument parsing from business logic. Enables `from renamer.core import preview, rename` from other scripts or tests without invoking the argument parser. Package structure also makes `pip install -e .` work cleanly.

## 3. Regex-based pattern matching vs. glob/fnmatch
- **Chosen:** Python `re` (regex)
- **Rejected:** `fnmatch`, `pathlib.glob()`, shell globs
- **Why:** Regex provides the most flexibility for rename patterns (capture groups, conditional replacements, lookaheads). Globs can't do `report_(\d{4}) → summary_\1`. The slight increase in complexity is worth it for power users.

## 4. Dry-run as a flag vs. separate subcommand
- **Chosen:** Both — `--dry-run` flag on `rename` AND a dedicated `preview` subcommand
- **Rejected:** Only one or the other
- **Why:** The `--dry-run` flag makes it easy to transition from preview to execution (just remove the flag). The `preview` subcommand gives a clearer, safer path for users who want to be explicit. Both share the same underlying logic.

## 5. Manifest store format (JSON vs. SQLite vs. YAML)
- **Chosen:** JSON flat file at `~/.renamer/manifest.json`
- **Rejected:** SQLite (overkill for a rename log), YAML (extra dependency), CSV (poor for nested data)
- **Why:** JSON is stdlib, human-readable, and trivially parsable. A rename manifest is small (<1 KB per operation). No external dependency needed.

## 6. Undo via manifest vs. git-like history vs. no undo
- **Chosen:** Manifest-based undo (last N operations)
- **Rejected:** Git-like hash chains, no undo feature
- **Why:** A rename manifest stores every `from→to` pair. Undo simply reverses each pair in reverse order. This is simpler than git-style snapshots and more reliable than no undo (which punishes mistakes).

## 7. Conflict resolution strategy
- **Chosen:** Append `_1`, `_2`, etc. suffix on collision
- **Rejected:** Overwrite, skip, ask interactively
- **Why:** Overwriting is destructive. Skipping without alternatives leaves files behind. Interactive mode doesn't work in scripts. Auto-suffix is safe, predictable, and scriptable. Files that collide with existing disk files also get suffixed.

## 8. Counter token format `{n}` vs. `{counter}` vs. `%d`
- **Chosen:** `{n}` and `{n:3}` (with optional zero-padding)
- **Rejected:** `{counter}` (verbose), `%d`/`%03d` (confusing with Python string formatting)
- **Why:** `{n}` is concise, `{n:3}` is intuitive for padding. The syntax is distinct enough from regex replacement groups `\1` to avoid confusion.

## 9. Counter increments per file that matches, not per file in directory
- **Chosen:** Counter increments only for files that pass the regex AND would change name
- **Rejected:** Counter increments for every file, including non-matches
- **Why:** If a directory has `a.txt`, `b.txt`, `c.txt` but the pattern only matches `a` and `c`, counter should produce `1` and `2`, not `1` and `3` with a gap.

## 10. pyproject.toml vs. setup.py vs. no installer
- **Chosen:** `pyproject.toml` with setuptools backend
- **Rejected:** `setup.py` (legacy), no installer (can't `pip install -e .`)
- **Why:** Modern Python packaging standard. `pyproject.toml` works with pip, allows `renamer` CLI entry point via `[project.scripts]`, and has zero build-time dependencies beyond setuptools.

## 11. Testing framework choice
- **Chosen:** `pytest` via `python -m pytest`
- **Rejected:** `unittest` standalone, `nose`
- **Why:** pytest is the community standard, works with zero config, and provides clear assertion introspection. Tests use temp directories for isolation — no mock filesystem needed.

## 12. Desktop notifications? No.
- **Chosen:** No notifications, quiet operation
- **Rejected:** `notify-send` / `osascript` popups
- **Why:** A batch renamer should be quiet and scriptable. Notifications interrupt flow and don't add value for a CLI utility.

## 13. Extension filter: dot-prefixed vs. bare extension input
- **Chosen:** Accept both `txt` and `.txt` — normalize internally
- **Rejected:** Require exactly one format
- **Why:** Users will type both. Normalizing to lowercase with leading dot removes a common friction point. The help text shows `--ext EXT`, leaving the format ambiguous on purpose.

## 14. Relative vs. absolute paths in manifest
- **Chosen:** Absolute paths in manifest
- **Rejected:** Relative paths
- **Why:** Relative paths break if the working directory changes between rename and undo. Absolute paths are stable regardless of where the user runs `renamer undo`.

## 15. File extension filter by suffix only (not full pattern)
- **Chosen:** `--ext` filters by file extension (lowercase, suffix match)
- **Rejected:** Glob-based filtering, full regex on filename
- **Why:** Extension filtering is the most common need ("rename only .jpg files"). A simple `.lower()` suffix check is fast and correct. Users who need more complex filtering can use `find | xargs renamer` or the regex pattern itself.