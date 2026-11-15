"""Table rendering and JSON output for probe results."""

from __future__ import annotations

import json
import sys
from typing import Any

from rich.box import SQUARE
from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text

from .models import ProbeResult

# ── status → colour / icon mappings ──────────────────────────────────────────

_STATUS_STYLE: dict[str, str] = {
    "OK": "green",
    "OPEN": "green",
    "FAIL": "red",
    "CLOSED": "red",
    "TIMEOUT": "yellow",
    "ERROR": "yellow",
}

_STATUS_ICON: dict[str, str] = {
    "OK": "\u2705",
    "OPEN": "\u2705",
    "FAIL": "\u274c",
    "CLOSED": "\u274c",
    "TIMEOUT": "\u26a0\ufe0f",
    "ERROR": "\u26a0\ufe0f",
}

_CONSOLE = Console()


def _status_cell(status: str) -> Text:
    """Return a styled Text object for the STATUS column."""
    colour = _STATUS_STYLE.get(status, "white")
    icon = _STATUS_ICON.get(status, "?")
    return Text(f" {icon} {status}", style=colour)


# ── table builder ────────────────────────────────────────────────────────────


def build_table(results: list[ProbeResult], host: str) -> Table:
    """Build a rich.Table from probe results."""
    table = Table(
        title=f"hostinger \u2014 host diagnostics for {host}",
        title_style="bold cyan",
        header_style="bold white",
        border_style="blue",
        box=SQUARE,
        show_lines=True,
        padding=(0, 1),
    )

    table.add_column("PROBE", style="cyan", no_wrap=True)
    table.add_column("STATUS", no_wrap=True)
    table.add_column("DETAILS")

    for r in results:
        table.add_row(r.probe, _status_cell(r.status), r.detail)

    return table


# ── output helpers ───────────────────────────────────────────────────────────


def print_table(results: list[ProbeResult], host: str) -> None:
    """Print the colourised table to stderr (keeping stdout clean)."""
    table = build_table(results, host)
    _CONSOLE.print(table)


def print_json(results: list[ProbeResult], host: str) -> None:
    """Print structured JSON to stdout."""
    output: dict[str, Any] = {
        "host": host,
        "results": [r.to_dict() for r in results],
    }
    json.dump(output, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


def print_output(
    results: list[ProbeResult],
    host: str,
    json_mode: bool = False,
) -> None:
    """Dispatch to the correct output format."""
    if json_mode:
        print_json(results, host)
    else:
        print_table(results, host)
