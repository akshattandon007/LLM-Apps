"""Data models for probe results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProbeResult:
    """Normalized result from a single diagnostic probe.

    Attributes:
        probe: Short label like "DNS", "Ping", "Port 80", "HTTP http".
        status: One of "OK", "FAIL", "TIMEOUT", "ERROR", "OPEN", "CLOSED".
        detail: Human-readable one-line summary for the table output.
        data: Structured dict with typed fields for JSON output.
    """

    probe: str
    status: str
    detail: str
    data: dict[str, Any] = field(default_factory=dict)

    @property
    def is_ok(self) -> bool:
        """True if the probe succeeded."""
        return self.status in ("OK", "OPEN")

    @property
    def is_fail(self) -> bool:
        """True if the probe failed."""
        return self.status in ("FAIL", "CLOSED", "TIMEOUT", "ERROR")

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict for JSON output."""
        return {
            "probe": self.probe,
            "status": self.status,
            "detail": self.detail,
            "data": self.data,
        }
