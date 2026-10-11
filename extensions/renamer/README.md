# Renamer 🏷️

**Batch file renamer with regex patterns, number sequences, and dry-run preview.**

> Stop renaming files one by one. Renamer applies regex-based transforms to entire directories with safe preview, collision handling, and one-command undo.

## Features

- 🔍 **Regex patterns** — capture groups, conditional replacements, anything `re.sub` can do
- 🔢 **Number sequences** — `{n}` for auto-counter, `{n:3}` for zero-padded (`001`, `002`…)
- 👁️ **Dry-run preview** — see exactly what would change before touching anything
- ⚡ **Live rename** — executes renames with conflict resolution (auto-suffixes collisions)
- ↩️ **Undo** — revert the last N rename operations from a persisted manifest
- 📋 **History** — view recent operations with timestamps
- 🎯 **Extension filter** — target only `.txt`, `.jpg`, etc.

## Installation

```bash
cd extensions/renamer
pip install -e .
```

Zero external dependencies — Python stdlib only.

## Usage

```bash
# Preview what would happen
renamer preview ./screenshots "Screenshot (\d{4})-(\d{2})-(\d{2})" "screenshot_\1\2\3"

# Live rename
renamer rename ./downloads "report_\d{4}" "final_report" --dry-run  # check first
renamer rename ./downloads "report_\d{4}" "final_report"             # go

# Number sequences
renamer rename ./photos "IMG_\d+" "vacation_{n:3}" --ext .jpg

# Undo a mistake
renamer undo

# See recent operations
renamer history
```

## Why Renamer?

- **Zero external dependencies** — works on any system with Python 3.10+
- **Safe by design** — dry-run always available, undo persists across sessions
- **Scriptable** — exit codes and stdout work in shell pipelines

## Project files

| File | Purpose |
|------|---------|
| `renamer/cli.py` | CLI argument parsing and dispatch |
| `renamer/core.py` | Rename logic, conflict resolution, manifest persistence |
| `tests/test_renamer.py` | Test suite (pytest) |
| `Decisions.md` | 15 architectural decisions with rejected alternatives |
| `Flow.md` | Function-level call chains and module dependency graph |