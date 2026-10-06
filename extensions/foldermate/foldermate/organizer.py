"""Organizes files into categorized folders with optional date subdirectories."""

import shutil
from pathlib import Path
from typing import List, Tuple

from .config import FolderMateConfig
from .scanner import FileInfo
from .undo import UndoLog


def plan_moves(
    files: List[FileInfo], config: FolderMateConfig
) -> List[Tuple[FileInfo, Path]]:
    """Determine the target paths for each file without moving anything.

    Returns list of (FileInfo, target_path) pairs.
    """
    source = config.source_dir.resolve()
    moves: List[Tuple[FileInfo, Path]] = []

    for f in files:
        target_dir = source

        if config.strategy in ("by-type", "both"):
            target_dir = target_dir / f.category

        if config.strategy in ("by-date", "both"):
            date_subdir = f.modified.strftime(config.date_format)
            if config.strategy == "both":
                target_dir = source / f.category / date_subdir
            else:
                target_dir = target_dir / date_subdir

        target_path = target_dir / f.name

        # Handle naming conflicts: append a counter if the target exists
        # and it's not the same file
        counter = 1
        while target_path.exists() and target_path.resolve() != f.path.resolve():
            stem = f.path.stem
            suffix = f.path.suffix
            target_path = target_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        # If the target IS the same file, skip it (already in right place)
        if target_path.resolve() == f.path.resolve():
            continue

        moves.append((f, target_path))

    return moves


def execute_moves(
    moves: List[Tuple[FileInfo, Path]], config: FolderMateConfig, undo: UndoLog
) -> int:
    """Move files from source to target, logging each move for undo."""
    moved_count = 0

    for f, target in moves:
        target.parent.mkdir(parents=True, exist_ok=True)

        if target.exists():
            # Shouldn't happen due to plan_moves conflict resolution,
            # but safeguard
            stem = f.path.stem
            suffix = f.path.suffix
            counter = 1
            while target.exists():
                target = target.parent / f"{stem}_{counter}{suffix}"
                counter += 1

        shutil.move(str(f.path), str(target))
        undo.log_move(str(f.path), str(target))
        moved_count += 1

    return moved_count