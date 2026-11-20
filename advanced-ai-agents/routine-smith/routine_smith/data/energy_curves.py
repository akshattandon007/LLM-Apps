"""Energy pattern curves for different chronotypes.

Defines the typical energy level at different times of day for morning,
night, and balanced chronotypes. Energy ranges from 0 (exhausted) to 10 (peak).
"""

from enum import Enum


class Chronotype(Enum):
    MORNING = "morning"   # Lark — peaks early
    NIGHT = "night"       # Owl — peaks late
    BALANCED = "balanced" # Neither extreme


# Energy levels (0-10) at hourly intervals from 5 AM to 1 AM (24-hour cycle)
ENERGY_CURVES = {
    Chronotype.MORNING: {
        5: 3, 6: 5, 7: 7, 8: 8, 9: 9, 10: 10,
        11: 9, 12: 8, 13: 7, 14: 6, 15: 6, 16: 5,
        17: 5, 18: 4, 19: 4, 20: 3, 21: 3, 22: 2,
        23: 1, 0: 1, 1: 0, 2: 0, 3: 0, 4: 1,
    },
    Chronotype.NIGHT: {
        5: 0, 6: 1, 7: 2, 8: 3, 9: 4, 10: 5,
        11: 5, 12: 6, 13: 6, 14: 7, 15: 7, 16: 8,
        17: 8, 18: 9, 19: 9, 20: 10, 21: 9, 22: 9,
        23: 8, 0: 7, 1: 6, 2: 5, 3: 4, 4: 2,
    },
    Chronotype.BALANCED: {
        5: 1, 6: 3, 7: 5, 8: 6, 9: 7, 10: 8,
        11: 8, 12: 7, 13: 7, 14: 6, 15: 6, 16: 6,
        17: 6, 18: 6, 19: 5, 20: 5, 21: 4, 22: 3,
        23: 2, 0: 1, 1: 0, 2: 0, 3: 0, 4: 1,
    },
}


TASK_ENERGY_MAP = {
    "high": (7, 10),
    "medium": (4, 7),
    "low": (1, 5),
}


def get_energy_at_hour(chronotype: Chronotype, hour: int) -> int:
    """Get energy level (0-10) for a given chronotype at a given hour."""
    curve = ENERGY_CURVES.get(chronotype, ENERGY_CURVES[Chronotype.BALANCED])
    return curve.get(hour, 3)


def is_task_compatible(chronotype: Chronotype, hour: int, required_energy_label: str) -> bool:
    """Check if a task's energy requirement matches the user's typical energy at that hour."""
    energy = get_energy_at_hour(chronotype, hour)
    low, high = TASK_ENERGY_MAP.get(required_energy_label, (1, 10))
    return low <= energy <= high


def best_hours_for_task(chronotype: Chronotype, required_energy_label: str) -> list[int]:
    """Get the best hours for a task with the given energy requirement."""
    low, high = TASK_ENERGY_MAP.get(required_energy_label, (1, 10))
    good_hours = []
    for hour in range(24):
        energy = get_energy_at_hour(chronotype, hour)
        if low <= energy <= high:
            good_hours.append(hour)
    return good_hours