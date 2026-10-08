#!/usr/bin/env python3
"""VibeCaster — Turn your mood into a full aesthetic experience.

Usage:
    python vibecaster.py
    python vibecaster.py "feeling tired but hopeful"
"""

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich import box
from rich.text import Text


# ── Data model ──────────────────────────────────────────────────────────────

@dataclass
class VibePackage:
    """The full response from the AI."""

    mood: str
    palette_hexes: list[str] = field(default_factory=list)
    palette_names: list[str] = field(default_factory=list)
    poem: str = ""
    playlist: list[dict[str, str]] = field(default_factory=list)  # [{title, artist, reason}]
    vibe_shift: str = ""
    description: str = ""


# ── API client ──────────────────────────────────────────────────────────────

class VibeClient:
    """OpenRouter-backed AI client for VibeCaster."""

    _client: Optional[OpenAI] = None  # Pre-declared for test patching

    MODELS = [
        "google/gemini-2.5-flash",
        "openai/gpt-4o-mini:free",
        "gryphe/mythomax-l2-13b:free",
        "openai/gpt-oss-20b:free",
    ]

    SYSTEM_PROMPT = """You are VibeCaster, a creative AI that turns moods into rich aesthetic experiences.
Given a mood or feeling, respond with valid JSON (no markdown fences, no commentary) following this schema exactly:

{
  "description": "A 1-sentence evocation of the vibe — what it feels like, what imagery it conjures.",
  "palette": [
    {"hex": "#NNNNNN", "name": "Descriptive color name"},
    ...
  ],
  "poem": "A short original poem (4-8 lines) capturing the mood.",
  "playlist": [
    {"title": "Song title", "artist": "Artist name", "reason": "Why this song fits the mood"},
    ...
  ],
  "vibe_shift": "A single concrete activity that shifts or deepens the mood — something the person can actually do in 5-15 minutes."
}

Rules:
- Palette must have 4-6 colours. Hexes should be aesthetic and cohesive.
- The poem must be original, not a famous quote.
- Playlist must have exactly 3 songs, existing real songs.
- Vibe_shift must be a real, actionable suggestion.
- Keep the total mood of the response cohesive — every element should feel like it belongs to the same world.
"""

    def __init__(self):
        api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            env_path = Path(os.environ.get("HOME", "/data")) / ".env"
            if env_path.exists():
                for line in env_path.read_text().splitlines():
                    if "OPENROUTER_API_KEY" in line:
                        api_key = line.split("=", 1)[1].strip()
                        break
        if not api_key:
            raise RuntimeError(
                "No API key found. Set OPENROUTER_API_KEY or OPENAI_API_KEY "
                "in your environment or .env file."
            )
        self.api_key = api_key
        self._client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )

    def generate(self, mood: str) -> VibePackage:
        """Call the LLM and parse the structured response."""
        response = self._client.chat.completions.create(
            model=self.MODELS[0],
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": f"Mood: {mood}"},
            ],
            temperature=0.8,
            max_tokens=1500,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            raw = raw.rsplit("```", 1)[0]
        data = json.loads(raw.strip())
        return VibePackage(
            mood=mood,
            palette_hexes=[c["hex"] for c in data.get("palette", [])],
            palette_names=[c["name"] for c in data.get("palette", [])],
            poem=data.get("poem", ""),
            playlist=data.get("playlist", []),
            vibe_shift=data.get("vibe_shift", ""),
            description=data.get("description", ""),
        )


# ── Terminal rendering ──────────────────────────────────────────────────────

console = Console()


def _colour_block(hex_code: str) -> Text:
    """Render a small coloured block in the terminal."""
    ansi_r = int(hex_code[1:3], 16) if len(hex_code) >= 7 else 128
    ansi_g = int(hex_code[3:5], 16)
    ansi_b = int(hex_code[5:7], 16)
    block = "  ●  "
    return Text(block, style=f"color({ansi_r},{ansi_g},{ansi_b})")


def render(vibe: VibePackage) -> None:
    """Render a VibePackage to the terminal with Rich formatting."""

    # ── Header ──
    console.print()
    console.rule(f"[bold magenta]🎨  VibeCaster[/] — {vibe.mood}", characters="~")
    console.print()

    # ── Description ──
    if vibe.description:
        console.print(Panel.fit(
            Markdown(vibe.description),
            border_style="dim white",
            box=box.ROUNDED,
        ))
        console.print()

    # ── Palette ──
    if vibe.palette_hexes:
        console.print("[bold cyan]🎨  Colour Palette[/]")
        swatches = []
        for hex_code, name in zip(vibe.palette_hexes, vibe.palette_names):
            swatches.append(f"{_colour_block(hex_code)}  [bold]{hex_code}[/]  {name}")
        console.print(Columns(swatches, equal=True, expand=False))
        console.print()

    # ── Poem ──
    if vibe.poem:
        console.print(Panel(
            Markdown(vibe.poem),
            title="[yellow]✍  Poem[/]",
            border_style="yellow",
            box=box.HEAVY,
        ))
        console.print()

    # ── Playlist ──
    if vibe.playlist:
        console.print("[bold cyan]🎵  3-Song Playlist[/]")
        for i, song in enumerate(vibe.playlist, 1):
            console.print(f"  {i}. [italic]{song.get('title', '?')}[/] — [bold]{song.get('artist', '?')}[/]")
            console.print(f"     [dim]{song.get('reason', '')}[/]")
        console.print()

    # ── Vibe shift ──
    if vibe.vibe_shift:
        console.print(Panel(
            Markdown(vibe.vibe_shift),
            title="[bold green]🌀  Vibe Shift[/]",
            border_style="green",
            box=box.ROUNDED,
        ))

    console.print()


# ── Entry point ─────────────────────────────────────────────────────────────

def main():
    mood = sys.argv[1] if len(sys.argv) > 1 else Prompt.ask(
        "[bold magenta]✨  How are you feeling?[/] Describe your mood"
    )
    if not mood or not mood.strip():
        console.print("[red]No mood entered. Exiting.[/]")
        sys.exit(1)

    mood = mood.strip()

    try:
        client = VibeClient()
    except RuntimeError as e:
        console.print(f"[red]❌  {e}[/]")
        sys.exit(1)

    with console.status("[bold cyan]Summoning your vibe package…[/]", spinner="moon"):
        try:
            vibe = client.generate(mood)
        except Exception as e:
            console.print(f"[red]❌  Vibe generation failed: {e}[/]")
            sys.exit(1)

    render(vibe)


if __name__ == "__main__":
    main()