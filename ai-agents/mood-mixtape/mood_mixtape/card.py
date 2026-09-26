"""Mixtape card formatter — beautiful console output for the Mood Mixtape."""

from __future__ import annotations

from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from .models import Mixtape


def _make_cover_art(mixtape: Mixtape) -> str:
    """Generate an ASCII-art style cover art representation."""
    lines = []
    lines.append("╔══════════════════════════════════════╗")
    lines.append("║                                      ║")
    lines.append("║       ┌─────────────────────┐        ║")
    lines.append("║       │      ♪ ♫ ♪ ♫ ♪      │        ║")
    lines.append("║       │                       │        ║")
    lines.append(f"║       │  {mixtape.playlist_name.center(21)}  │        ║")
    lines.append("║       │                       │        ║")
    lines.append("║       │     MOOD MIXTAPE      │        ║")
    lines.append("║       │                       │        ║")
    lines.append("║       └─────────────────────┘        ║")
    lines.append("║                                      ║")
    lines.append("╚══════════════════════════════════════╝")
    return "\n".join(lines)


def format_mixtape(mixtape: Mixtape) -> str:
    """Format the mixtape as a beautiful console string using Rich markup."""
    console = Console(width=72, force_terminal=True)

    # Collect renderables
    elements = []

    # Title
    title = Text()
    title.append("🎵 ", style="bold")
    title.append("MOOD MIXTAPE", style="bold bright_magenta")
    title.append(" 🎵", style="bold")
    elements.append(Align(title, align="center"))
    elements.append(Rule(style="bright_magenta"))

    # Mood header
    mood_text = Text()
    mood_text.append(f"Mood: ", style="bold white")
    mood_text.append(f"{mixtape.mood}", style="bold cyan")
    mood_text.append(f"\n{mixtape.mood_description}", style="italic bright_black")
    elements.append(Panel(mood_text, border_style="cyan"))

    # Cover art
    cover_text = Text()
    cover_text.append("COVER ART", style="bold yellow")
    cover_text.append(f"\n{_make_cover_art(mixtape)}")
    cover_text.append(f"\nPrompt: ", style="italic bright_black")
    cover_text.append(f"{mixtape.cover_art_description}", style="bright_black")
    elements.append(Panel(cover_text, border_style="yellow"))

    # Playlist info
    info_text = Text()
    info_text.append("🎧 ", style="bold green")
    info_text.append(f"{mixtape.playlist_name}", style="bold green")
    info_text.append(f"\n{mixtape.vibe_description}", style="italic white")
    elements.append(Panel(info_text, border_style="green"))

    # Songs table
    table = Table(show_header=True, header_style="bold bright_blue", border_style="blue")
    table.add_column("#", style="dim", width=3)
    table.add_column("Song", style="white", width=28)
    table.add_column("Artist", style="cyan", width=20)
    table.add_column("Why It Fits", style="italic bright_black", width=25, overflow="fold")

    for i, song in enumerate(mixtape.songs, 1):
        table.add_row(
            str(i),
            song.title,
            song.artist,
            song.why_it_fits,
        )

    elements.append(Panel(table, title="[bold]Tracklist[/bold]", border_style="bright_blue"))

    # Footer
    elements.append(Text(f"\n✨ Curated by Mood Mixtape • {len(mixtape.songs)} tracks", style="dim"))

    # Render
    output_lines = []
    console.capture()
    for element in elements:
        with console.capture() as capture:
            console.print(element)
        output_lines.append(capture.get())

    return "\n".join(output_lines)


def print_mixtape(mixtape: Mixtape) -> None:
    """Print the formatted mixtape to console."""
    console = Console()
    console.print(format_mixtape(mixtape))