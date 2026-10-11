# Flow.md — Renamer

## Entry point → CLI → Core → Filesystem

```
pyproject.toml [project.scripts]
  └── renamer = "renamer.cli:main"
        │
        ▼
renamer/cli.py :: main()
  │  parse_args() → argparse subcommand
  │
  ├── rename ▸  cli.py::rename(…)
  │                │
  │                ▼
  │              core.py::rename(directory, pattern, replacement, …)
  │                │
  │                ├── core.py::preview(directory, pattern, …)
  │                │     │
  │                │     ├── Path(directory).iterdir() / rglob(*)    ──► read dir
  │                │     ├── filter by is_file() + ext match        ──► filter
  │                │     ├── core.py::_apply_rename_rule(name, …)   ──► regex sub
  │                │     │     └── re.sub(pattern, replacement)      ──► transform
  │                │     │     └── {n} / {n:WIDTH} → str(counter)   ──► counter
  │                │     ├── core.py::_resolve_conflicts(pairs)     ──► dedup
  │                │     └── return [(src, dest, ok), …]            ──► results
  │                │
  │                ├── if dry_run: return results                    ──► no-op
  │                │
  │                └── for each (src, dest, ok):                     ──► execute
  │                      src.rename(dest)                            ──► filesystem
  │                      append to manifest_entry["changes"]
  │                      │
  │                      ▼
  │                    core.py::_load_manifest()
  │                    core.py::_save_manifest()                     ──► ~/.renamer/manifest.json
  │
  ├── preview ▸  cli.py::print_results(results, dry_run=True)
  │                │
  │                └── core.py::preview(…)  (same path as above, no execution)
  │
  ├── undo ▸  core.py::undo(limit)
  │              │
  │              ├── _load_manifest()                                 ──► read JSON
  │              ├── for entry in reversed(manifest)[:limit]:
  │              │     for change in reversed(changes):
  │              │         dst.rename(src)                            ──► revert
  │              └── _save_manifest(trimmed)                          ──► persist
  │
  └── history ▸ core.py::history()
                   │
                   └── _load_manifest()
                       for entry in reversed(manifest)[:limit]:
                           print(…)
```

## Module dependency graph

```
renamer/__init__.py     (version string only)
       │
renamer/cli.py          (argparse, CLI dispatch)
       │
       └── renamer.core
             │
             ├── renamer.core._apply_rename_rule()
             ├── renamer.core._resolve_conflicts()
             ├── renamer.core.preview()
             ├── renamer.core.rename()
             ├── renamer.core.undo()
             ├── renamer.core.history()
             ├── renamer.core._load_manifest()
             └── renamer.core._save_manifest()
```

## Data flow diagram

```
User input (args)
    │
    ▼
argparse namespace
    │
    ▼
core.py functions
    │
    ├── directory listing ──────────────────────────────────► os / pathlib
    ├── regex transform                                     │
    │     re.sub(pattern, replacement, filename)            │
    │     ↓                                                 │
    │     new_name (string with optional {n} expanded)      │
    ├── conflict resolution                                 │
    │     ↓                                                 │
    │     [(src, dest), ...]                                │
    ├── execute rename (if not dry-run)                     │
    │     src.rename(dest)                                  │
    │     │                                                 │
    │     └── log change → manifest.json                    │
    └── print results                                       │
          stdout                                            │
                                                            ▼
                                                  Terminal output
```

## Key execution paths

| Path | Trigger | Files affected | Manifest updated |
|------|---------|---------------|-----------------|
| **Dry-run preview** | `renamer rename ... --dry-run` or `renamer preview ...` | None (read-only) | No |
| **Live rename** | `renamer rename dir pattern replacement` | Yes | Yes |
| **Undo** | `renamer undo [N]` | Yes (reverts) | Yes (removed) |
| **History** | `renamer history` | None | No |

## Counter token processing in `_apply_rename_rule`

```
replacement string: "photo_{n:3}"
                      ↓
        re.search(r"\{n(:(\d+))?\}", replacement)
                      ↓
        match groups:  (n:3)         (3)
                      ↓
        str(counter).zfill(3)  →  "001"
                      ↓
        replacement: "photo_001"
```

## Conflict resolution in `_resolve_conflicts`

```
Input: [(src="a.txt", "out.txt"), (src="b.txt", "out.txt")]
                ↓
"out.txt" already used → "b.txt" → "out_1.txt"
                ↓
Output: [(a.txt → out.txt), (b.txt → out_1.txt)]

Also checks disk: if "out.txt" already exists, "out_2.txt" is tried.
```