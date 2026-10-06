# Decisions.md — FolderMate

## 1. Python over Rust or Go

**Chosen:** Python 3.10+
**Rejected:** Rust (too heavy for a simple file utility), Go (steeper build toolchain)
**Why:** FolderMate is a file-management utility with zero performance-critical loops — `shutil.move` is I/O-bound, not CPU-bound. Python's `pathlib` and `shutil` provide everything needed out of the box, and the target audience (everyday people) can install it with `pip`. No compilation step means faster iteration and broader platform support.

## 2. CLI tool over GUI/web app

**Chosen:** CLI with argparse
**Rejected:** Flask web UI, Tkinter GUI, browser extension
**Why:** File organization is a one-shot task — users run it occasionally, not continuously. A GUI adds launch complexity and a dependency chain. A CLI tool pairs naturally with `cron` or manual invocation and works in headless environments (servers, CI). The dry-run mode gives safe preview without the overhead of a web server.

## 3. Dry-run first by default

**Chosen:** `--mode dry-run` is the default
**Rejected:** Requiring explicit `--dry-run` flag, or executing immediately
**Why:** Moving files is destructive — a bad organization could scatter files. Defaulting to dry-run gives users a safe preview (which files go where) before committing. The `--mode execute` flag is an explicit opt-in to actual moves. This handles the #1 user fear: "will it mess up my files?"

## 4. Category-based sorting over custom rules

**Chosen:** Predefined categories (Documents, Images, Audio, Video, Archives, Code, Installers, Fonts, Torrents, Others)
**Rejected:** User-defined regex/pattern matching, AI-based classification
**Why:** Predefined categories cover 95%+ of real-world files with zero config. Adding a YAML config file for custom rules would be scope-creep for v1. AI-based classification is overkill and adds dependency weight. The extension→category mapping is a single dict users can extend by editing `config.py` if they need customisation.

## 5. Three organization strategies (by-type, by-date, both)

**Chosen:** Three strategies available via `--by-type`, `--by-date`, `--both`
**Rejected:** Single strategy, or inferring strategy from file metadata
**Why:** Different users prefer different mental models. "By type" is the most intuitive (all PDFs in Documents/), "by date" helps chronological cleanup (month folders), and "both" gives fine-grained nesting. Letting the user choose, with `by-type` as default, covers all common organisation patterns.

## 6. Skip list to prevent re-organizing organized folders

**Chosen:** A hardcoded `skip_dirs` list in config matches category folder names
**Rejected:** Relying on `.nomedia` / `.organized` marker files, or no skip logic
**Why:** The #1 foot-gun with recursive file organizers is that they recurse into the folders they just created, attempting to re-organize the organized files in endless loops. The skip list prevents this by skipping any path segment that matches a known category folder name. Marker files (`.organized`) would require creating extra files, which is invasive.

## 7. `execute_moves` uses `shutil.move` over `os.rename`

**Chosen:** `shutil.move()`
**Rejected:** `os.rename()`, `pathlib.Path.rename()`, or `subprocess mv`
**Why:** `shutil.move` handles cross-filesystem moves (e.g., moving from `~/Downloads` to an external drive or a Docker volume). `os.rename` fails with `EXDEV` if source and target are on different filesystems. `subprocess mv` would be platform-specific.

## 8. Undo log as append-only text file

**Chosen:** `|||`-separated log in `~/.foldermate/undo.log`
**Rejected:** SQLite database, JSON log, git-based undo
**Why:** An append-only text log is trivially inspectable (`cat ~/.foldermate/undo.log`), works with `grep`, and survives corruption better than a binary format. The `|||` separator was chosen to be unlikely in file paths. A full SQLite DB adds a dependency for a 1-move-per-line use case. Git-based undo would be overkill and confusing.

## 9. Undo reverses newest moves first

**Chosen:** Reverse-order undo (last moved → first restored)
**Rejected:** Forward-order undo, timestamp-based selective undo
**Why:** Moves are logged in order. If files A → A' and B → B' were moved, reversing (B' → B then A' → A) restores the filesystem to its original state without conflicts. Forward-order would try to restore A' → A while B' might be in the way. Selective undo by timestamp would require additional tracking data.

## 10. Name conflict resolution with counter suffix

**Chosen:** `file_1.pdf`, `file_2.pdf` when target exists
**Rejected:** Overwrite silently, skip conflicting files, hash-based disambiguation
**Why:** Silent data loss (overwrite) is unacceptable. Skipping leaves files stranded. Hash-based naming is opaque to users. A numbered suffix is intuitive and immediately tells the user there was a conflict without needing to open a log.

## 11. pip-installable package over standalone script

**Chosen:** `pyproject.toml` with `[project.scripts]` entry point
**Rejected:** Single `foldermate.py` script, `setup.py`
**Why:** A properly packaged CLI tool installs cleanly (`pip install .`), registers a `foldermate` command in PATH, and supports virtual environments. A single script would require manual PATH management. `setup.py` is deprecated in favour of `pyproject.toml`.

## 12. `undo` as a subcommand over a separate script

**Chosen:** `foldermate undo` subcommand
**Rejected:** Separate `foldermate-undo` script, `--undo` flag on main command
**Why:** A subcommand keeps undo close to the main tool (single entry point, shared log path logic). A separate script would need duplicate config parsing. An `--undo` flag would conflict with positional arguments and confuse the command-line interface.

## 13. No external dependencies

**Chosen:** Pure stdlib (`argparse`, `pathlib`, `shutil`, `datetime`)
**Rejected:** `click`, `rich`, `typer`, `pydantic`
**Why:** This tool copies files around — it doesn't need HTTP requests, async I/O, or fancy formatting. Zero-dependency means `pip install` is instant, no lockfile to maintain, and no supply-chain attack surface. `pytest` is only a dev dependency.

## 14. Tests mirror real file operations (not mocks)

**Chosen:** `tmp_path` fixtures with real file creation and actual `plan_moves` calls
**Rejected:** Mocking `Path` and `shutil` calls
**Why:** File operations are I/O-simple and creating temp files is fast. Real file operations in tests catch edge cases (symlinks, permission errors, filesystem boundaries) that mocks would miss. The `tmp_path` fixture provides isolation without mocks.