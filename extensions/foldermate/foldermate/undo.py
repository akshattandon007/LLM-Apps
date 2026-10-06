"""Undo log for FolderMate — tracks moves so users can reverse them."""

import shutil
from pathlib import Path
from typing import List, Tuple


class UndoLog:
    """Manages an append-only log of file moves for undo."""

    SEPARATOR = "|||"

    def __init__(self, log_path: Path):
        self.log_path = log_path

    def log_move(self, source: str, destination: str) -> None:
        """Append a move record to the log."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a") as f:
            f.write(f"{source}{self.SEPARATOR}{destination}\n")

    def read_log(self) -> List[Tuple[str, str]]:
        """Read all move records in order (oldest first)."""
        if not self.log_path.exists():
            return []
        entries: List[Tuple[str, str]] = []
        with open(self.log_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(self.SEPARATOR, 1)
                if len(parts) == 2:
                    entries.append((parts[0], parts[1]))
        return entries

    def undo(self) -> int:
        """Reverse all moves (newest first). Returns count of files restored."""
        if not self.log_path.exists():
            print("No undo log found — nothing to undo.")
            return 0

        entries = self.read_log()
        undone = 0

        # Reverse order (last moved → first restored)
        for source, destination in reversed(entries):
            dest_path = Path(destination)
            source_path = Path(source)

            if not dest_path.exists():
                # Already moved or deleted
                continue

            source_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dest_path), str(source_path))
            undone += 1

        # Clear the log after undoing
        self.log_path.unlink(missing_ok=True)
        return undone

    def clear(self) -> None:
        """Remove the undo log."""
        self.log_path.unlink(missing_ok=True)