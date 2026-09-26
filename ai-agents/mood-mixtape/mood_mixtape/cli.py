"""CLI entry point for Mood Mixtape."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

import rich

from .card import print_mixtape
from .curator import analyze_mood, curate_mixtape
from .models import Track
from .musicbrainz import search_by_mood_keywords


def _get_mood_keywords(mood_analysis: dict) -> list[str]:
    """Extract search keywords from mood analysis, with sensible defaults."""
    keywords = mood_analysis.get("search_keywords", [])
    genres = mood_analysis.get("genres", [])
    # Combine keywords + genres for a richer search
    all_terms: list[str] = []
    for k in keywords:
        # Clean up — remove quotation marks
        all_terms.append(k.strip('"\''))
    for g in genres:
        all_terms.append(g.strip("'\""))
    return all_terms if all_terms else ["popular"]


def run(mood: Optional[str] = None, interactive: bool = False) -> None:
    """Run the Mood Mixtape pipeline.

    Args:
        mood: A mood description string. If None and interactive is False,
              prompts via stdin.
        interactive: If True, runs in interactive mode with prompts.
    """
    mood_input = mood

    if interactive or not mood_input:
        try:
            mood_input = input("🎵 How are you feeling right now? Describe your mood: ").strip()
        except (EOFError, KeyboardInterrupt):
            rich.print("[red]Aborted.[/red]")
            sys.exit(1)

    if not mood_input:
        rich.print("[red]Please provide a mood description![/red]")
        sys.exit(1)

    rich.print(f"\n[bold cyan]Analyzing mood:[/bold cyan] \"[italic]{mood_input}[/italic]\"\n")

    # Step 1: LLM analyzes the mood
    mood_analysis = analyze_mood(mood_input)
    mood_label = mood_analysis.get("mood", mood_input)
    mood_desc = mood_analysis.get("description", "")
    rich.print(f"[bold]Detected mood:[/bold] {mood_label}")
    rich.print(f"[dim]{mood_desc}[/dim]\n")

    # Step 2: Search MusicBrainz for tracks matching mood keywords
    keywords = _get_mood_keywords(mood_analysis)
    rich.print(f"[bold]Searching MusicBrainz for:[/bold] {', '.join(keywords)}")

    tracks: list[Track] = search_by_mood_keywords(keywords, limit=40)

    if not tracks:
        rich.print("[yellow]No results from MusicBrainz search. Trying broader search...[/yellow]")
        tracks = search_by_mood_keywords(["popular", "recording"], limit=30)

    if not tracks:
        rich.print("[red]Could not find any tracks. Check internet connection.[/red]")
        sys.exit(1)

    rich.print(f"[green]Found {len(tracks)} tracks. Curating mixtape...[/green]\n")

    # Step 3: LLM curates the mixtape
    mixtape = curate_mixtape(mood_input, tracks)

    # Step 4: Print the beautiful mixtape card
    print_mixtape(mixtape)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="🎵 Mood Mixtape — Generate a personalized mixtape based on your mood.",
    )
    parser.add_argument(
        "mood",
        nargs="?",
        help="Describe your mood (e.g., 'stressed after work', 'euphoric spring morning')",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Run in interactive mode with prompts",
    )

    args = parser.parse_args()

    if not args.mood and not args.interactive:
        parser.print_help()
        print("\nExample: mood-mixtape \"feeling nostalgic about summer road trips\"")
        print("         mood-mixtape -i")
        sys.exit(0)

    run(mood=args.mood, interactive=args.interactive)


if __name__ == "__main__":
    main()