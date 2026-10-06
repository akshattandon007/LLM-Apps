"""CLI entry point for FolderMate."""

import argparse
import shutil
import sys
from pathlib import Path

from . import __version__, __app_name__
from .config import FolderMateConfig
from .scanner import scan_directory
from .organizer import plan_moves, execute_moves
from .undo import UndoLog


def _human_size(bytes_: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if bytes_ < 1024:
            return f"{bytes_:.1f} {unit}"
        bytes_ /= 1024
    return f"{bytes_:.1f} TB"


def _print_summary(moves, config):
    """Print a formatted summary of planned/executed moves."""
    by_category: dict[str, list] = {}
    total_size = 0

    for f, target in moves:
        cat = f.category
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append((f, target))
        total_size += f.size_bytes

    print(f"\n{'='*60}")
    print(f"  {__app_name__} v{__version__}")
    print(f"  Mode: {config.mode.upper()}  |  Strategy: {config.strategy}")
    print(f"  Source: {config.source_dir.resolve()}")
    print(f"{'='*60}")

    total_files = len(moves)
    print(f"\n  📦 {total_files} file{'s' if total_files != 1 else ''} to organize")
    if config.mode == "dry-run":
        print(f"  💾 ~{_human_size(total_size)} to move")
    print()

    for cat in sorted(by_category.keys()):
        items = by_category[cat]
        size = sum(f.size_bytes for f, _ in items)
        print(f"  📁 {cat}/  ({len(items)} files, {_human_size(size)})")
        if config.verbose:
            for f, target in items:
                rel_target = target.relative_to(config.source_dir.resolve())
                print(f"      {f.name}  →  {rel_target}")
        print()

    print(f"{'='*60}")


def _run_undo(log_path_str):
    """Run the undo subcommand."""
    log_path = Path(log_path_str) if log_path_str else Path.home() / ".foldermate" / "undo.log"
    undo = UndoLog(log_path)
    count = undo.undo()
    if count > 0:
        print(f"✅ Undone {count} file move{'s' if count != 1 else ''}.")
    else:
        print("ℹ️  Nothing to undo.")


def main():
    # Quick check for undo subcommand before parsing
    if len(sys.argv) >= 2 and sys.argv[1] == "undo":
        log_path = None
        if len(sys.argv) >= 4 and sys.argv[2] == "--log":
            log_path = sys.argv[3]
        _run_undo(log_path)
        return

    parser = argparse.ArgumentParser(
        prog=__app_name__.lower(),
        description="Organize messy folders by file type and/or date.",
        epilog="Example: foldermate ~/Downloads --mode dry-run --by-type --verbose",
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to organize (default: current dir)",
    )
    parser.add_argument(
        "--mode",
        choices=["dry-run", "execute"],
        default="dry-run",
        help="'dry-run' previews changes; 'execute' actually moves files (default: dry-run)",
    )
    parser.add_argument(
        "--by-type",
        action="store_const",
        dest="strategy",
        const="by-type",
        help="Organize into type folders (Documents/, Images/, etc.)",
    )
    parser.add_argument(
        "--by-date",
        action="store_const",
        dest="strategy",
        const="by-date",
        help="Organize into date folders (2025-01/, 2025-02/, etc.)",
    )
    parser.add_argument(
        "--both",
        action="store_const",
        dest="strategy",
        const="both",
        help="Organize into Type/Date subfolders",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files (starting with .)",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_false",
        dest="recursive",
        help="Only process top-level files, don't recurse into subdirs",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show individual file moves",
    )
    parser.add_argument(
        "--log",
        help="Path to undo log file (default: ~/.foldermate/undo.log)",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version and exit",
    )

    args = parser.parse_args()

    if args.version:
        print(f"{__app_name__} v{__version__}")
        return

    # Build config
    config = FolderMateConfig(
        source_dir=Path(args.directory).resolve(),
        mode=args.mode,
        strategy=args.strategy or "by-type",
        include_hidden=args.include_hidden,
        recursive=args.recursive if hasattr(args, "recursive") else True,
        verbose=args.verbose,
        undo_log=Path(args.log) if args.log else Path.home() / ".foldermate" / "undo.log",
    )

    # Scan
    try:
        files = scan_directory(config)
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    if not files:
        print("ℹ️  No files found to organize.")
        return

    # Plan
    moves = plan_moves(files, config)

    if not moves:
        print("✅ Everything is already organized — nothing to move.")
        return

    # Show summary
    _print_summary(moves, config)

    # Execute or dry-run
    if config.mode == "execute":
        undo = UndoLog(config.undo_log)
        count = execute_moves(moves, config, undo)
        print(f"\n✅ Moved {count} file{'s' if count != 1 else ''}.")
        print(f"📝 Undo log: {config.undo_log}")
    else:
        print(f"\n💡 Run with --mode execute to apply these changes.")
        print(f"   Or: {__app_name__.lower()} {config.source_dir} --mode execute")


if __name__ == "__main__":
    main()