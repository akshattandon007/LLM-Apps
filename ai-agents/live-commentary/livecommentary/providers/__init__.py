"""Provider registry.

New providers register themselves here so the CLI can construct them by name.
"""

from __future__ import annotations

from typing import Callable, Dict

from .base import MatchProvider


def _make_espn(**kw) -> MatchProvider:
    from .espn import ESPNProvider

    return ESPNProvider(
        sport=kw.get("sport", "soccer"),
        league=kw.get("league", "eng.1"),
    )


def _make_football_data(**kw) -> MatchProvider:
    from .football_data import FootballDataProvider

    return FootballDataProvider(api_key=kw.get("api_key"))


def _make_simulated(**kw) -> MatchProvider:
    from .simulated import SimulatedProvider

    return SimulatedProvider(speed=float(kw.get("speed", 30.0)))


REGISTRY: Dict[str, Callable[..., MatchProvider]] = {
    "espn": _make_espn,
    "football-data": _make_football_data,
    "simulated": _make_simulated,
}


def create_provider(name: str, **kwargs) -> MatchProvider:
    """Instantiate a provider by registry name."""
    try:
        factory = REGISTRY[name]
    except KeyError:
        raise ValueError(
            f"Unknown provider {name!r}. Available: {', '.join(sorted(REGISTRY))}"
        )
    return factory(**kwargs)


__all__ = ["MatchProvider", "create_provider", "REGISTRY"]
