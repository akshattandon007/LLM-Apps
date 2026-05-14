"""
Spotify Mood Agent — CLI entry point.

Usage:
    python -m src.main
    python -m src.main --tracks 30 --verbose
    python -m src.main --output report.md --format markdown
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from src.agent.mood_agent import MoodAgent
from src.spotify.auth import check_auth_status, get_spotify_client
from src.spotify.client import SpotifyClient
from src.utils.display import make_progress_spinner, print_report, print_tool_call

load_dotenv()

console = Console()
logging.basicConfig(level=logging.WARNING)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mood-agent",
        description="Predict your mood from Spotify listening history using AI.",
    )
    parser.add_argument(
        "--tracks",
        type=int,
        default=50,
        metavar="N",
        help="Number of recent tracks to analyse (default: 50, max: 200)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        metavar="FILE",
        help="Save report to file (e.g. report.md)",
    )
    parser.add_argument(
        "--format",
        choices=["rich", "json", "markdown"],
        default="rich",
        help="Output format (default: rich)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show agent reasoning steps",
    )
    parser.add_argument(
        "--cache",
        type=str,
        default=".spotify_token_cache",
        help="Path to Spotify token cache file",
    )
    return parser.parse_args()


def cli() -> None:
    args = parse_args()

    if args.verbose:
        logging.getLogger("src").setLevel(logging.INFO)

    console.print()
    console.print("[bold cyan]🎵 Spotify Mood Agent[/bold cyan]", justify="center")
    console.print("[dim]Powered by Claude AI + Spotify API[/dim]", justify="center")
    console.print()

    # ── Auth ──
    try:
        sp = get_spotify_client(cache_path=args.cache)
        user = check_auth_status(sp)
        console.print(f"  ✅ Connected as [bold]{user['display_name']}[/bold] "
                      f"([dim]{user['product']}[/dim])")
    except EnvironmentError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Spotify auth failed:[/red] {e}")
        console.print("[dim]Run: python scripts/authenticate.py[/dim]")
        sys.exit(1)

    # ── Fetch tracks ──
    spotify = SpotifyClient(sp)

    with make_progress_spinner("Fetching your recent tracks...") as progress:
        progress.add_task("fetch")
        try:
            session = spotify.get_recently_played(limit=args.tracks)
        except Exception as e:
            console.print(f"[red]Failed to fetch tracks:[/red] {e}")
            sys.exit(1)

    if session.track_count == 0:
        console.print("[yellow]No recently played tracks found.[/yellow]")
        console.print("Make sure you've listened to Spotify recently.")
        sys.exit(0)

    console.print(
        f"  📀 Fetched [bold]{session.track_count}[/bold] tracks "
        f"([bold]{len(session.tracks_with_features)}[/bold] with audio features)"
    )
    console.print()

    # ── Run agent ──
    def on_tool_call(tool_name: str, tool_input: dict) -> None:
        if args.verbose:
            print_tool_call(tool_name, tool_input)

    agent = MoodAgent(verbose=args.verbose, on_tool_call=on_tool_call)

    with make_progress_spinner("Agent is analysing your listening history...") as progress:
        task = progress.add_task("analyse")
        if not args.verbose:
            try:
                report = agent.analyse(session)
            except Exception as e:
                console.print(f"[red]Analysis failed:[/red] {e}")
                sys.exit(1)
        else:
            progress.stop()
            try:
                report = agent.analyse(session)
            except Exception as e:
                console.print(f"[red]Analysis failed:[/red] {e}")
                sys.exit(1)

    # ── Output ──
    if args.output:
        output_path = Path(args.output)
        # Determine format from extension if not specified
        fmt = args.format
        if output_path.suffix == ".md" and fmt == "rich":
            fmt = "markdown"
        elif output_path.suffix == ".json" and fmt == "rich":
            fmt = "json"

        from io import StringIO
        from rich.console import Console as RichConsole

        file_console = RichConsole(file=StringIO(), no_color=True, width=100)

        if fmt == "markdown":
            from src.utils.display import _to_markdown
            output_path.write_text(_to_markdown(report))
        elif fmt == "json":
            output_path.write_text(report.model_dump_json(indent=2))
        else:
            print_report(report, format=fmt)

        console.print(f"  💾 Report saved to [bold]{output_path}[/bold]")
    else:
        print_report(report, format=args.format)


if __name__ == "__main__":
    cli()
