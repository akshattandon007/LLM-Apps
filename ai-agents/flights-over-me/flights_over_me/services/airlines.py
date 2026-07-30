"""Resolve airline identity from a callsign.

A callsign like ``BAW123`` starts with the 3-letter ICAO airline designator
(``BAW`` = British Airways). We map that prefix to a friendly name using a
bundled dataset. The dataset ships with major carriers; drop in a fuller
ICAO airline table (e.g. from OpenFlights) to widen coverage.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "airlines.json"
_CALLSIGN_RE = re.compile(r"^([A-Z]{3})(\d.*)?$")


@lru_cache(maxsize=1)
def _airline_table() -> dict[str, str]:
    with _DATA_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def airline_icao_from_callsign(callsign: str | None) -> str | None:
    """Extract the 3-letter ICAO airline code from a callsign, if present."""
    if not callsign:
        return None
    match = _CALLSIGN_RE.match(callsign.strip().upper())
    return match.group(1) if match else None


def resolve_airline(callsign: str | None) -> tuple[str | None, str | None]:
    """Return ``(icao_code, airline_name)`` for a callsign.

    The name is ``None`` when the prefix isn't in our table — we still return
    the code so the UI can show *something* useful.
    """
    icao = airline_icao_from_callsign(callsign)
    if icao is None:
        return None, None
    return icao, _airline_table().get(icao)
