"""Rules engine — maps weather conditions to packing items.

Uses a YAML rules file (default: bundled rules.yaml) with threshold-based rules.
Each rule defines conditions under which an item is recommended.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from packlight.weather import DayWeather

# Default rules bundled with the package
DEFAULT_RULES_PATH = Path(__file__).parent.parent / "rules.yaml"


@dataclass
class PackItem:
    """A single packing recommendation."""
    category: str
    item: str
    reason: str


class PackingEngine:
    """Evaluates weather data against a set of packing rules."""

    def __init__(self, rules_path: str | None = None) -> None:
        self._rules_path = Path(rules_path) if rules_path else DEFAULT_RULES_PATH
        self._rules: list[dict[str, Any]] = []
        self._load_rules()

    def _load_rules(self) -> None:
        """Load rules from the YAML file."""
        path = self._rules_path
        if not path.exists():
            # Fallback: look in the package directory
            path = Path(__file__).parent.parent / "rules.yaml"
        if not path.exists():
            raise FileNotFoundError(
                f"Rules file not found at {self._rules_path} or {path}"
            )
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        self._rules = data.get("rules", [])
        self._categories = data.get("categories", [])

    def generate(self, days: list[DayWeather]) -> list[PackItem]:
        """Generate a packing list from weather data.

        Evaluates all rules against the aggregated trip weather.
        Returns a list of PackItem, deduplicated and grouped by category.
        """
        if not days:
            return []

        # Aggregate weather across the trip
        agg = self._aggregate(days)
        selected: list[PackItem] = []

        for rule in self._rules:
            match = self._evaluate_rule(rule, agg)
            if match:
                selected.append(PackItem(
                    category=rule.get("category", "General"),
                    item=rule["item"],
                    reason=rule.get("reason", ""),
                ))

        return selected

    def _aggregate(self, days: list[DayWeather]) -> dict[str, Any]:
        """Aggregate per-day weather into trip-level stats."""
        return {
            "max_temp": max(d.temp_max_c for d in days),
            "min_temp": min(d.temp_min_c for d in days),
            "avg_max_temp": sum(d.temp_max_c for d in days) / len(days),
            "avg_min_temp": sum(d.temp_min_c for d in days) / len(days),
            "total_precip": sum(d.precipitation_mm for d in days),
            "max_precip_day": max(d.precipitation_mm for d in days),
            "rain_days": sum(1 for d in days if d.precipitation_mm > 0.5),
            "max_wind": max(d.wind_speed_max_kmh for d in days),
            "avg_wind": sum(d.wind_speed_max_kmh for d in days) / len(days),
            "max_uv": max(d.uv_index_max for d in days),
            "min_daylight": min(d.daylight_hours for d in days),
            "snow_any": any(
                d.weather_code in {71, 73, 75, 77, 85, 86}
                for d in days
            ),
            "thunder_any": any(d.weather_code in {95, 96, 99} for d in days),
            "fog_any": any(d.weather_code in {45, 48} for d in days),
            "trip_days": len(days),
        }

    def _evaluate_rule(
        self, rule: dict[str, Any], agg: dict[str, Any]
    ) -> bool:
        """Evaluate a single rule's conditions against aggregated weather."""
        conditions = rule.get("conditions", {})
        if not conditions:
            return False

        for metric, threshold in conditions.items():
            actual = agg.get(metric)
            if actual is None:
                continue  # skip unknown metrics

            if isinstance(threshold, dict):
                op = threshold.get("op", ">=")
                value = threshold["value"]
            else:
                op = ">="
                value = threshold

            if op == ">=" and not (actual >= value):
                return False
            elif op == ">" and not (actual > value):
                return False
            elif op == "<=" and not (actual <= value):
                return False
            elif op == "<" and not (actual < value):
                return False
            elif op == "==" and not (actual == value):
                return False
            elif op == "!=" and not (actual != value):
                return False
            elif op == "any":
                # 'any' expects a list of possible values, actual is bool
                if not actual:
                    return False

        return True