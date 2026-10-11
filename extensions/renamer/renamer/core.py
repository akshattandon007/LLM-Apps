"""
Renamer core — handles renaming logic, pattern application, preview, and undo.
"""

import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

MANIFEST_DIR = Path.home() / ".renamer"
MANIFEST_FILE = MANIFEST_DIR / "manifest.json"


def _ensure_manifest() -> None:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    if not MANIFEST_FILE.exists():
        MANIFEST_FILE.write_text("[]")


def _load_manifest() -> List[Dict]:
    _ensure_manifest()
    try:
        return json.loads(MANIFEST_FILE.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save_manifest(entries: List[Dict]) -> None:
    _ensure_manifest()
    MANIFEST_FILE.write_text(json.dumps(entries, indent=2))


# ── Pattern helpers ────────────────────────────────────────────────


def _apply_rename_rule(
    original: str, pattern: str, replacement: str, counter: int
) -> str:
    """Apply a regex substitution with optional counter token support.

    Applies substitution to the filename stem only (before the last dot)
    so patterns like ``\\w+`` don't accidentally match the extension.  # noqa: W605
    """
    # Support {n} token for zero-padded counter
    if "{n" in replacement:
        m = re.search(r"\{n(:(\d+))?\}", replacement)
        if m:
            width = int(m.group(2)) if m.group(2) else 0
            token = m.group(0)
            padded = str(counter).zfill(width) if width else str(counter)
            replacement = replacement.replace(token, padded)

    stem, ext = os.path.splitext(original)
    new_stem = re.sub(pattern, replacement, stem)
    return new_stem + ext


def _resolve_conflicts(pairs: List[Tuple[Path, str]]) -> List[Tuple[Path, Path]]:
    """
    Resolve naming conflicts by appending suffixes.
    Returns list of (source, destination) where source always wins.
    """
    resolved = []
    used_names: Dict[str, int] = {}

    for src, new_name in pairs:
        dest = src.parent / new_name
        stem = dest.stem
        suffix = dest.suffix

        if new_name in used_names:
            count = used_names[new_name] + 1
            used_names[new_name] = count
            dest = src.parent / f"{stem}_{count}{suffix}"
        elif dest.exists() and src != dest:
            # File already exists on disk — uniquify
            count = 1
            while (src.parent / f"{stem}_{count}{suffix}").exists():
                count += 1
            dest = src.parent / f"{stem}_{count}{suffix}"

        used_names[new_name] = used_names.get(new_name, 1)
        resolved.append((src, dest))

    return resolved


# ── Core operations ────────────────────────────────────────────────


def preview(
    directory: str,
    pattern: str,
    replacement: str,
    recursive: bool = False,
    file_ext: Optional[str] = None,
    start_num: int = 1,
) -> List[Tuple[Path, Path, bool]]:
    """
    Preview what would happen. Returns list of (source, destination, ok).
    ok=True means rename would proceed; ok=False means collision.
    """
    base = Path(directory).expanduser().resolve()
    if not base.is_dir():
        print(f"Error: {directory} is not a directory.", file=sys.stderr)
        sys.exit(1)

    if recursive:
        paths = sorted(base.rglob("*"))
    else:
        paths = sorted(base.iterdir())

    # Filter to regular files and optionally by extension
    targets = [p for p in paths if p.is_file()]
    if file_ext:
        ext = file_ext if file_ext.startswith(".") else f".{file_ext}"
        targets = [p for p in targets if p.suffix.lower() == ext.lower()]

    pairs: List[Tuple[Path, str]] = []
    counter = start_num
    for p in targets:
        new_name = _apply_rename_rule(p.name, pattern, replacement, counter)
        if new_name == p.name:
            counter += 1
            continue  # No change — skip
        pairs.append((p, new_name))
        counter += 1

    resolved = _resolve_conflicts(pairs)
    results: List[Tuple[Path, Path, bool]] = []
    for src, dest in resolved:
        collision = dest.exists() and src != dest
        results.append((src, dest, not collision))

    return results


def rename(
    directory: str,
    pattern: str,
    replacement: str,
    recursive: bool = False,
    file_ext: Optional[str] = None,
    start_num: int = 1,
    dry_run: bool = False,
) -> List[Tuple[Path, Path, bool]]:
    """
    Execute renames. In dry_run mode, only show what would happen.
    Returns list of (source, destination, success).
    """
    results = preview(directory, pattern, replacement, recursive, file_ext, start_num)

    if not results:
        return results

    if dry_run:
        return results

    manifest_entry = {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "directory": str(Path(directory).expanduser().resolve()),
        "pattern": pattern,
        "replacement": replacement,
        "changes": [],
    }

    success_results = []
    for src, dest, ok in results:
        if not ok:
            print(f"  ⚠  COLLISION: {src.name} → {dest.name} (skipped)")
            continue
        try:
            src.rename(dest)
            manifest_entry["changes"].append(
                {"from": str(src), "to": str(dest)}
            )
            success_results.append((src, dest, True))
        except OSError as e:
            print(f"  ✗  FAILED: {src.name} → {dest.name}: {e}", file=sys.stderr)
            success_results.append((src, dest, False))

    # Save undo manifest
    if manifest_entry["changes"]:
        manifest = _load_manifest()
        manifest.append(manifest_entry)
        _save_manifest(manifest)

    return success_results


def undo(limit: int = 1) -> int:
    """Undo the last N rename operations from the manifest."""
    manifest = _load_manifest()
    if not manifest:
        print("No rename operations to undo.")
        return 0

    reversed_entries = list(reversed(manifest))
    undone_count = 0

    for entry in reversed_entries[:limit]:
        changes = entry["changes"]
        reverted = 0
        for change in reversed(changes):
            src = Path(change["from"])
            dst = Path(change["to"])
            if dst.exists():
                try:
                    dst.rename(src)
                    reverted += 1
                except OSError as e:
                    print(f"  ✗  Undo FAILED: {dst.name} → {src.name}: {e}")
            else:
                print(f"  ⚠  {dst.name} no longer exists — skipping")
        print(f"  ✓  Undid {reverted}/{len(changes)} renames from {entry['timestamp']}")
        undone_count += 1

    # Remove undone entries from manifest
    manifest = manifest[: len(manifest) - undone_count]
    _save_manifest(manifest)

    return undone_count


def history(limit: int = 10) -> None:
    """Show recent rename operations from the manifest."""
    manifest = _load_manifest()
    if not manifest:
        print("No rename history found.")
        return

    for entry in reversed(manifest)[:limit]:
        count = len(entry["changes"])
        print(
            f"  [{entry['timestamp']}] "
            f"{entry['directory']} : "
            f"\"{entry['pattern']}\" → \"{entry['replacement']}\" "
            f"({count} file{'s' if count != 1 else ''})"
        )