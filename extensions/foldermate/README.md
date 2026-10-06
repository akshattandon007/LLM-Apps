# FolderMate 🗂️

**Organize your messy Downloads, Desktop, or any folder — by file type, by date, or both.**

FolderMate scans a directory, categorizes every file by its extension (Documents, Images, Audio, Video, Archives, Code, etc.), and shows you exactly what it would move where — before touching anything.

```bash
# Preview what would happen
foldermate ~/Downloads --mode dry-run

# Actually organize it
foldermate ~/Downloads --mode execute

# Undo if you don't like it
foldermate undo
```

## Features

- 🧠 **Smart categories** — PDFs → Documents/, .jpg → Images/, .py → Code/, 90+ extensions mapped
- 📅 **Date organization** — `--by-date` sorts into 2025-01/, 2025-02/, etc. by modification time
- 🔀 **Combined** — `--both` gives Type/Date nesting (Documents/2025-06/)
- 👁️ **Safe dry-run by default** — preview every move before committing
- ↩️ **Full undo** — every move is logged; `foldermate undo` reverses the entire operation
- 🏷️ **Smart conflict handling** — `file_1.pdf`, `file_2.pdf` when names collide
- 🔒 **No dependencies** — pure Python stdlib, works offline, zero install fuss

## Install

```bash
pip install .
```

Or use it directly from the repo:

```bash
cd /data/LLM-Apps/extensions/foldermate
pip install -e .
```

## Usage

```
foldermate [directory] [options]

Commands:
  foldermate [dir]      Organize files (default: dry-run mode)
  foldermate undo       Reverse the last organization

Options:
  --mode dry-run        Preview changes (default)
  --mode execute        Actually move files
  --by-type             Organize into Documents/, Images/, etc. (default)
  --by-date             Organize into YYYY-MM/ date folders
  --both                Organize into Type/YYYY-MM/ subfolders
  --include-hidden      Also process hidden files (.*)
  --no-recursive        Only scan top-level, skip subdirectories
  --verbose, -v         Show every individual file move
```

### Examples

```bash
# See what would happen to your Desktop
foldermate ~/Desktop

# Actually organize Downloads by type
foldermate ~/Downloads --mode execute

# Organize by date (month folders)
foldermate ~/Downloads --by-date --mode execute

# Organize by type then date
foldermate ~/Pictures --both --mode execute --verbose

# Undo the entire operation
foldermate undo
```

## Project Structure

```
foldermate/
├── foldermate/          # Source package
│   ├── __init__.py      # Version info
│   ├── cli.py           # CLI entry point & output formatting
│   ├── config.py        # File type categories & configuration
│   ├── scanner.py       # Directory scanning & categorization
│   ├── organizer.py     # Move planning & execution
│   └── undo.py          # Move logging & undo logic
├── tests/
│   ├── test_scanner.py  # Scanner & categorization tests
│   └── test_organizer.py # Planner, executor & undo tests
├── Decisions.md         # Architectural decisions & trade-offs
├── Flow.md              # Execution flow & module dependency graph
├── pyproject.toml       # Package config
└── README.md            # This file
```

## Undo Log

Moves are logged to `~/.foldermate/undo.log`. The log is append-only text in the format `source|||destination`, making it trivially inspectable and grep-able. Running `foldermate undo` reverses all moves (newest-first) and clears the log.

## License

MIT