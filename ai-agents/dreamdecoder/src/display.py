"""Terminal display helpers for rich output."""

from __future__ import annotations

import shutil
from typing import Optional

from .models import DreamEntry, DreamStats


def _term_width() -> int:
    return shutil.get_terminal_size(fallback=(80, 24)).columns


def _rule(char: str = "─", title: str = "") -> str:
    width = _term_width()
    if title:
        available = width - len(title) - 4
        if available > 4:
            left = char * (available // 2)
            right = char * (available - available // 2)
            return f"{left} {title} {right}"
    return char * width


def print_entry(entry: DreamEntry, detailed: bool = True) -> None:
    """Display a formatted dream entry."""
    print()
    print(_rule("─", f" Dream: {entry.id} "))
    print(f"  📅  {entry.date[:19].replace('T', ' · ')}")
    print(f"\n  💭  {entry.dream_text}")
    if entry.tags:
        print(f"\n  🏷️   {'  '.join(entry.tags)}")
    if entry.interpretation and detailed:
        inter = entry.interpretation
        if inter.symbols:
            print(f"\n  🔍  Symbols: {', '.join(f'[{s}]' for s in inter.symbols)}")
        if inter.mood and inter.mood != "unknown":
            print(f"  🌗  Mood: {inter.mood.upper()}")
        if inter.themes:
            print(f"  📌  Themes: {', '.join(inter.themes)}")
        print(f"\n  📖  Interpretation:\n{_indent(inter.interpretation)}")
    print(_rule("─"))
    print()


def _indent(text: str, spaces: int = 4) -> str:
    """Indent multi-line text."""
    prefix = " " * spaces
    return "\n".join(f"{prefix}{line}" for line in text.strip().split("\n"))


def print_entry_list(entries: list[DreamEntry]) -> None:
    """Display a compact list of entries."""
    if not entries:
        print("\n  📭  No dream entries yet. Start one with: python main.py log\n")
        return
    print(f"\n  📖  Dream Journal — {len(entries)} entr{'y' if len(entries) == 1 else 'ies'}")
    print(_rule("·"))
    for i, entry in enumerate(entries, 1):
        date_str = entry.date[:10]
        preview = entry.dream_text[:60] + "..." if len(entry.dream_text) > 60 else entry.dream_text
        symbols = ""
        if entry.interpretation and entry.interpretation.symbols:
            symbols = f"  [{', '.join(entry.interpretation.symbols[:3])}]"
        print(f"  {i:3d}. [{entry.id}] {date_str}  {preview}{symbols}")
    print(_rule("·"))
    print()


def print_stats(stats: DreamStats) -> None:
    """Display aggregated dream statistics."""
    print()
    print(_rule("═", " DreamDecoder — Insights "))
    print(f"\n  📊  Total entries:  {stats.total_entries}")
    if stats.first_date:
        print(f"  📅  First entry:   {stats.first_date[:10]}")
    if stats.last_date:
        print(f"  📅  Latest entry:  {stats.last_date[:10]}")
    if stats.top_symbols:
        print(f"\n  🔍  Top Symbols:")
        for sym, count in stats.top_symbols:
            print(f"       {sym:20s}  {count:3d}x")
    if stats.top_themes:
        print(f"\n  📌  Top Themes:")
        for theme, count in stats.top_themes:
            print(f"       {theme:20s}  {count:3d}x")
    if stats.mood_distribution:
        print(f"\n  🌗  Mood Distribution:")
        total = sum(stats.mood_distribution.values())
        bar_max = 20
        for mood, count in stats.mood_distribution.items():
            pct = count / total * 100 if total > 0 else 0
            bar = "█" * max(1, int(pct / 100 * bar_max))
            print(f"       {mood:15s}  {bar}  {count:3d} ({pct:4.0f}%)")
    print(_rule("═"))
    print()


def print_welcome() -> None:
    """Display the welcome banner."""
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║      🌙  DREAM DECODER  🌟           ║")
    print("  ║   AI-Powered Dream Journal &         ║")
    print("  ║   Symbolic Interpretation            ║")
    print("  ╚══════════════════════════════════════╝")
    print()
    print("  Commands:  log    — Record and interpret a dream")
    print("             list   — Browse your dream journal")
    print("             view   — View a specific entry")
    print("             search — Search entries by keyword")
    print("             stats  — Show dream pattern insights")
    print("             delete — Remove an entry")
    print("             clear  — Clear all entries")
    print()


def print_success(action: str, detail: str = "") -> None:
    """Print a success message."""
    print(f"\n  ✅  {action}")
    if detail:
        print(f"      {detail}")
    print()