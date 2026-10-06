# Flow.md — FolderMate

## Execution Flow

### Primary path: `foldermate ~/Downloads --mode dry-run`

```
CLI entry: foldermate/cli.py:main()
  │
  ├─ argparse parses args → FolderMateConfig
  │
  ├─ foldermate/scanner.py:scan_directory(config)
  │   │
  │   ├─ Iterates source_dir with rglob(*) or glob(*)
  │   │   Filters: is_file(), !hidden (unless --include-hidden),
  │   │            !in skip_dirs
  │   │
  │   │   For each file:
  │   │   ├─ foldermate/scanner.py:_get_category(ext)
  │   │   │   └─ _build_ext_map() → extension-to-category dict (cached)
  │   │   │
  │   │   └─ Creates FileInfo(path, name, ext, category, size, modified)
  │   │
  │   └─ Returns sorted List[FileInfo]
  │
  ├─ foldermate/organizer.py:plan_moves(files, config)
  │   │
  │   │  For each FileInfo:
  │   │  ├─ Builds target_dir based on strategy:
  │   │  │   by-type:   source / category/
  │   │  │   by-date:   source / date_subdir/
  │   │  │   both:      source / category / date_subdir/
  │   │  │
  │   │  ├─ Resolves naming conflicts (counter suffix)
  │   │  │
  │   │  └─ Skips if target == source (already in place)
  │   │
  │   └─ Returns List[(FileInfo, target_path)]
  │
  ├─ foldermate/cli.py:_print_summary(moves, config)
  │   │
  │   └─ Groups moves by category, prints formatted table
  │
  └─ (if execute mode) → foldermate/organizer.py:execute_moves(moves, config, undo)
      │
      │  For each (FileInfo, target):
      │  ├─ target.parent.mkdir(parents=True, exist_ok=True)
      │  ├─ shutil.move(str(source), str(target))
      │  └─ undo.log_move(source, target)
      │
      └─ Returns moved count
```

### Undo path: `foldermate undo`

```
CLI entry: foldermate/cli.py:main() → _run_undo(args)
  │
  ├─ UndoLog(log_path)
  │   │
  │   ├─ undo_log.read_log() → List[(source, destination)] (oldest first)
  │   │
  │   └─ Iterates REVERSED:
  │       ├─ shutil.move(str(destination), str(source))
  │       └─ count++
  │
  ├─ log_path.unlink()  # Clear the log
  └─ Prints count of restored files
```

## Module Dependency Graph

```
foldermate/
│
├─ cli.py ─────────────► config.py
│                        scanner.py (scan_directory)
│                        organizer.py (plan_moves, execute_moves)
│                        undo.py (UndoLog)
│
├─ config.py            (no deps within package — pure data)
│
├─ scanner.py ─────────► config.py (CATEGORY_EXTENSIONS, FolderMateConfig)
│
├─ organizer.py ───────► config.py (FolderMateConfig)
│                        scanner.py (FileInfo)
│                        undo.py (UndoLog)
│
└─ undo.py              (no deps within package — pure stdlib)
```

## Data Flow

```
User input (directory path + flags)
  │
  ▼
argparse → FolderMateConfig
  │  source_dir, mode, strategy, ...
  ▼
scan_directory(config)
  │
  ▼
List[FileInfo] ← each has: .path, .name, .extension, .category, .size, .modified
  │
  ▼
plan_moves(files, config)
  │
  ▼
List[(FileInfo, target_path)]
  │  Example: (FileInfo("~/Downloads/report.pdf"), "~/Downloads/Documents/report.pdf")
  │
  ▼
_print_summary(moves) ──► terminal output (dry-run)
  │
  ──► execute_moves(moves) ──► shutil.move per file ──► undo.log (append)
```

## Key Design Decisions in Code

| Function | What it does | Why important |
|---|---|---|
| `_get_category(ext)` | Maps extension → category w/ cached reverse dict | Avoids O(n*m) lookup per file — built once |
| `plan_moves()` | Pure function, no side effects | Dry-run and execute share the same logic; testable without touching disk |
| `execute_moves()` | Performs moves + logs | Side-effect-only; separated from planning for testing |
| `UndoLog.log_move()` | Appends to `|||`-sep file | Append-only = crash-safe; undoing reverses |
| `_print_summary()` | Groups by category | Solves "where did my files go?" UX problem |