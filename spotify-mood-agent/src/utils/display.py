"""
Rich terminal output for the mood report.
"""

from __future__ import annotations

import json

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import box
from rich.text import Text

from src.spotify.models import MoodReport

console = Console()


ARC_ARROWS = {
    "up": "📈",
    "down": "📉",
    "stable": "➡️",
    "volatile": "〰️",
}

CONFIDENCE_COLOUR = {
    (0.0, 0.5): "red",
    (0.5, 0.7): "yellow",
    (0.7, 0.85): "green",
    (0.85, 1.01): "bright_green",
}


def _confidence_colour(c: float) -> str:
    for (lo, hi), colour in CONFIDENCE_COLOUR.items():
        if lo <= c < hi:
            return colour
    return "white"


def _bar(value: float, width: int = 20) -> str:
    filled = round(value * width)
    return "█" * filled + "░" * (width - filled)


def print_report(report: MoodReport, format: str = "rich") -> None:
    """Print the mood report to the terminal."""
    if format == "json":
        console.print_json(report.model_dump_json(indent=2))
        return
    if format == "markdown":
        console.print(_to_markdown(report))
        return

    # ── Rich terminal display ──
    console.print()
    console.rule("[bold cyan]🎵 SPOTIFY MOOD ANALYSIS[/bold cyan]")
    console.print()

    # Session info
    duration_str = (
        f"{report.session_duration_hours:.1f} hours"
        if report.session_duration_hours
        else "unknown duration"
    )
    console.print(
        f"  Analysed [bold]{report.tracks_analysed}[/bold] tracks "
        f"from the last [dim]{duration_str}[/dim]"
    )
    console.print()

    # Primary mood + confidence
    conf_colour = _confidence_colour(report.confidence)
    conf_pct = f"{report.confidence * 100:.0f}%"

    mood_table = Table(box=None, show_header=False, padding=(0, 2))
    mood_table.add_column("label", style="dim", width=22)
    mood_table.add_column("value", style="bold")
    mood_table.add_row("PRIMARY MOOD", f"[bold magenta]{report.primary_mood}[/bold magenta]")
    mood_table.add_row("CONFIDENCE", f"[{conf_colour}]{conf_pct}[/{conf_colour}]")
    mood_table.add_row("ENERGY LEVEL", f"{report.energy_level:.1f} / 10")
    arc_arrow = ARC_ARROWS.get(report.arc_direction, "")
    mood_table.add_row("EMOTIONAL ARC", f"{arc_arrow} {report.emotional_arc}")
    mood_table.add_row("DOMINANT MODE", report.dominant_mode.title())
    console.print(mood_table)
    console.print()

    # Audio feature bars
    console.rule("[dim]AUDIO SIGNATURE[/dim]")
    console.print()
    features = [
        ("Valence (happiness)", report.avg_valence),
        ("Energy", report.avg_energy),
        ("Danceability", report.avg_danceability),
        ("Acousticness", report.avg_acousticness),
        ("Instrumentalness", report.avg_instrumentalness),
    ]
    feature_table = Table(box=None, show_header=False, padding=(0, 2))
    feature_table.add_column("label", style="dim", width=28)
    feature_table.add_column("bar", no_wrap=True)
    feature_table.add_column("pct", style="dim", width=6)
    for label, val in features:
        feature_table.add_row(label, f"[cyan]{_bar(val)}[/cyan]", f"{val * 100:.0f}%")
    console.print(feature_table)
    console.print(f"  [dim]Avg Tempo:[/dim] [bold]{report.avg_tempo:.0f} BPM[/bold]")
    console.print()

    # Genres
    if report.top_genres:
        genre_str = " · ".join(f"[italic]{g}[/italic]" for g in report.top_genres[:5])
        console.print(f"  [dim]TOP GENRES:[/dim]  {genre_str}")
        console.print()

    # Insight
    console.rule("[dim]INSIGHT[/dim]")
    console.print()
    console.print(Panel(report.insight, padding=(1, 3), border_style="dim"))
    console.print()

    # Recommendations
    if report.recommendations:
        console.rule("[dim]WHAT TO LISTEN TO NEXT[/dim]")
        console.print()
        for rec in report.recommendations[:3]:
            console.print(f"  🎵 {rec}")
        console.print()

    console.rule()
    console.print()


def print_tool_call(tool_name: str, tool_input: dict) -> None:
    """Print a tool invocation in verbose mode."""
    label_map = {
        "get_track_list": "📋 Examining track list",
        "get_audio_feature_stats": "📊 Analysing audio features",
        "get_mood_trajectory": "📈 Computing mood trajectory",
        "get_genre_analysis": "🎸 Investigating genres",
        "get_track_deep_dive": "🔍 Deep-diving recent tracks",
        "synthesise_mood": "🧠 Synthesising mood prediction",
    }
    label = label_map.get(tool_name, f"🔧 {tool_name}")
    console.print(f"  [dim]{label}...[/dim]")


def make_progress_spinner(description: str = "Analysing your listening history...") -> Progress:
    """Return a Rich progress spinner."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    )


def _to_markdown(report: MoodReport) -> str:
    """Render the report as a markdown string."""
    genres = ", ".join(report.top_genres[:5]) if report.top_genres else "—"
    recs = "\n".join(f"- {r}" for r in report.recommendations)
    return f"""# 🎵 Spotify Mood Analysis

## Summary
| | |
|---|---|
| **Primary Mood** | {report.primary_mood} |
| **Confidence** | {report.confidence * 100:.0f}% |
| **Energy Level** | {report.energy_level:.1f} / 10 |
| **Emotional Arc** | {report.emotional_arc} |
| **Dominant Mode** | {report.dominant_mode.title()} |
| **Tracks Analysed** | {report.tracks_analysed} |

## Audio Features
| Feature | Score |
|---|---|
| Valence (happiness) | {report.avg_valence:.2f} |
| Energy | {report.avg_energy:.2f} |
| Danceability | {report.avg_danceability:.2f} |
| Acousticness | {report.avg_acousticness:.2f} |
| Instrumentalness | {report.avg_instrumentalness:.2f} |
| Avg Tempo | {report.avg_tempo:.0f} BPM |

**Top Genres:** {genres}

## Insight
{report.insight}

## Recommendations
{recs}
"""
