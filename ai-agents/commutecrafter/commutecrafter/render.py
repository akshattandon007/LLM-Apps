"""Terminal rendering. Text-first, colour only where it earns its keep."""

from __future__ import annotations

import json
from typing import Any, Sequence

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import ContentItem, Plan
from .timing import format_duration
from .weather import weather_note

SEGMENT_ICONS = {"warm-up": "☕", "core": "🧠", "wind-down": "🌙"}
SOURCE_COLOURS = {
    "wikipedia": "cyan",
    "arxiv": "magenta",
    "hackernews": "yellow",
    "gutenberg": "green",
}


def _fit_badge(plan: Plan) -> Text:
    delta = plan.delta_seconds
    if plan.fits:
        sign = "+" if delta >= 0 else "-"
        return Text(f"✔ fits  ({sign}{abs(delta)}s)", style="bold green")
    return Text(f"✘ off by {format_duration(abs(delta))}", style="bold red")


def render_plan(plan: Plan, console: Console | None = None, show_summary: bool = True) -> None:
    """Print a plan as three labelled tables with a header."""
    console = console or Console()

    header = Table.grid(padding=(0, 2))
    header.add_column(justify="right", style="dim")
    header.add_column()
    header.add_row("window", f"[bold]{plan.minutes:g} min[/bold] ({format_duration(plan.target_seconds)})")
    header.add_row("planned", f"[bold]{plan.total_seconds / 60:.1f} min[/bold] ({format_duration(plan.total_seconds)})")
    header.add_row("mode", plan.mode + (f" · {plan.transport}" if plan.transport else ""))
    header.add_row("status", _fit_badge(plan))

    blocks: list[Any] = [header]
    if plan.weather:
        blocks.append(Text(weather_note(plan.weather, plan.mode), style="dim"))
    console.print(Panel(Group(*blocks), title="CommuteCrafter", border_style="blue", expand=False))

    for segment in plan.segments:
        icon = SEGMENT_ICONS.get(segment.name, "•")
        table = Table(
            title=f"{icon} {segment.name.upper()}  ·  budget {format_duration(segment.budget_seconds)}",
            title_justify="left",
            show_lines=False,
            expand=True,
            pad_edge=False,
        )
        table.add_column("#", style="dim", width=2)
        table.add_column("time", justify="right", width=7, style="bold")
        table.add_column("item", overflow="fold")
        table.add_column("src", width=11)
        for idx, sched in enumerate(segment.items, start=1):
            colour = SOURCE_COLOURS.get(sched.item.source, "white")
            title = Text(sched.item.title)
            if sched.partial:
                title.append(f"  [{int(sched.fraction * 100)}%]", style="bold red")
            table.add_row(
                str(idx),
                format_duration(sched.seconds),
                title,
                Text(sched.item.source, style=colour),
            )
        console.print(table)
        for sched in segment.items:
            console.print(f"   [dim]↳[/dim] {sched.item.url}", highlight=False, soft_wrap=True)
            if sched.reason:
                console.print(f"     [dim italic]{sched.reason}[/dim italic]", highlight=False, soft_wrap=True)
        console.print()

    if plan.warnings:
        console.print("[yellow]notes:[/yellow]")
        for warn in plan.warnings:
            console.print(f"  • {warn}")

    if show_summary:
        used = {s.item.source for s in plan.scheduled_items}
        console.print(
            f"[dim]{len(plan.scheduled_items)} items across {len(used)} source(s). "
            f"Tolerance ±{plan.tolerance_seconds}s.[/dim]"
        )


def render_items(items: Sequence[ContentItem], console: Console | None = None, title: str = "Results") -> None:
    console = console or Console()
    if not items:
        console.print("[yellow]No items found.[/yellow]")
        return
    table = Table(title=title, title_justify="left", expand=True)
    table.add_column("item", overflow="fold")
    table.add_column("src", width=11)
    table.add_column("words", justify="right", width=7)
    table.add_column("read", justify="right", width=7)
    for item in items:
        table.add_row(
            item.title,
            Text(item.source, style=SOURCE_COLOURS.get(item.source, "white")),
            str(item.words),
            format_duration(round(item.words / 230 * 60)),
        )
    console.print(table)
    for item in items:
        console.print(f"   [dim]↳[/dim] {item.url}", highlight=False, soft_wrap=True)


def render_history(rows: Sequence[dict[str, Any]], console: Console | None = None) -> None:
    console = console or Console()
    if not rows:
        console.print("[yellow]No plans yet. Run `commutecrafter plan`.[/yellow]")
        return
    import datetime as _dt

    table = Table(title="Recent plans", title_justify="left", expand=True)
    table.add_column("when", width=17)
    table.add_column("window", justify="right", width=8)
    table.add_column("planned", justify="right", width=8)
    table.add_column("mode", width=7)
    table.add_column("items", justify="right", width=6)
    for row in rows:
        when = _dt.datetime.fromtimestamp(row["created_at"]).strftime("%Y-%m-%d %H:%M")
        table.add_row(
            when,
            f"{row['minutes']:g}m",
            f"{row['total_seconds'] / 60:.1f}m",
            row["mode"],
            str(len(row["items"])),
        )
    console.print(table)


def plan_json(plan: Plan, indent: int = 2) -> str:
    """Stable JSON for piping into other tools / tests."""
    return json.dumps(plan.to_dict(), indent=indent, ensure_ascii=False)
