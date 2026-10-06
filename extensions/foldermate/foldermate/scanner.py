"""Scans a directory and categorizes files for FolderMate."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .config import CATEGORY_EXTENSIONS, FolderMateConfig

# Cache the extension → category mapping once
_EXT_TO_CAT: Optional[Dict[str, str]] = None


def _build_ext_map() -> Dict[str, str]:
    """Build a reverse mapping from extension to category name."""
    mapping: Dict[str, str] = {}
    for category, exts in CATEGORY_EXTENSIONS.items():
        for ext in exts:
            # Lowercase extension as key
            mapping[ext.lower()] = category
    return mapping


def _get_category(ext: str) -> str:
    """Return the category for a file extension, or 'Others'."""
    global _EXT_TO_CAT
    if _EXT_TO_CAT is None:
        _EXT_TO_CAT = _build_ext_map()
    return _EXT_TO_CAT.get(ext.lower(), "Others")


@dataclass
class FileInfo:
    """Information about a discovered file."""
    path: Path
    name: str
    extension: str
    category: str
    size_bytes: int
    modified: datetime


def scan_directory(config: FolderMateConfig) -> List[FileInfo]:
    """Scan the source directory and return categorized file info.

    Returns files (not directories) sorted by name, excluding hidden files
    and directories on the skip list.
    """
    files: List[FileInfo] = []
    source = config.source_dir.resolve()

    if not source.exists():
        raise FileNotFoundError(f"Directory not found: {source}")
    if not source.is_dir():
        raise NotADirectoryError(f"Not a directory: {source}")

    # Determine glob pattern
    if config.recursive:
        iterator = source.rglob("*")
    else:
        iterator = source.glob("*")

    for item in iterator:
        if not item.is_file():
            continue

        # Skip hidden files (starting with .) unless asked
        if not config.include_hidden and item.name.startswith("."):
            continue

        # Skip files in skip_dirs (when recursive)
        if config.recursive:
            rel = item.relative_to(source)
            parts = rel.parts[:-1]  # parent directories relative to source
            if any(p in config.skip_dirs for p in parts):
                continue

        ext = item.suffix.lower()
        category = _get_category(ext)
        mtime = datetime.fromtimestamp(item.stat().st_mtime)

        files.append(FileInfo(
            path=item,
            name=item.name,
            extension=ext,
            category=category,
            size_bytes=item.stat().st_size,
            modified=mtime,
        ))

    files.sort(key=lambda f: f.name.lower())
    return files