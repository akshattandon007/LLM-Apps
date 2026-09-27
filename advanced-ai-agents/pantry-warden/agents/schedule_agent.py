"""ScheduleAgent — plans meals across the week respecting time windows."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional


class TimeSlot:
    """A cooking window on a given day."""
    def __init__(self, day: str, start_hour: int, end_hour: int,
                 label: str = ""):
        self.day = day
        self.start_hour = start_hour
        self.end_hour = end_hour
        self.label = label or f"{day} {start_hour}:00-{end_hour}:00"

    def duration_minutes(self) -> int:
        return (self.end_hour - self.start_hour) * 60


class ScheduleAgent:
    """Specialized agent that fits meals into a user's weekly schedule.

    Capabilities:
    - Match cook times to available time slots
    - Distribute meals across the week evenly
    - Avoid repeating same meals back-to-back
    - Handle meal type (breakfast/lunch/dinner) mapping
    """

    DAYS = ["monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday"]

    def __init__(self):
        self.slots: List[TimeSlot] = []
        self._plan: Dict[str, List[Dict]] = {d: [] for d in self.DAYS}

    def set_slots(self, slots: List[TimeSlot]):
        self.slots = slots

    def generate_week_slots(self, weekdays_only: bool = True,
                            dinners_per_week: int = 7,
                            breakfasts_per_week: int = 5,
                            lunches_per_week: int = 5) -> List[TimeSlot]:
        """Generate default time slots based on typical meal times."""
        slots = []
        days = self.DAYS[:5] if weekdays_only else self.DAYS

        for day in days:
            if breakfasts_per_week > 0:
                slots.append(TimeSlot(day, 7, 8, label=f"{day} breakfast"))
                breakfasts_per_week -= 1
            if lunches_per_week > 0:
                slots.append(TimeSlot(day, 12, 13, label=f"{day} lunch"))
                lunches_per_week -= 1
            if dinners_per_week > 0:
                slots.append(TimeSlot(day, 18, 19, label=f"{day} dinner"))
                dinners_per_week -= 1

        self.slots = slots
        return slots

    def fit_meal_to_slot(self, recipe: Dict, slot: TimeSlot) -> bool:
        """Check if a recipe fits in a time slot."""
        return recipe.get("cook_time_min", 30) <= slot.duration_minutes()

    def plan_week(self, recipes: List[Dict],
                  meal_type_preferences: Optional[Dict[str, str]] = None
                  ) -> Dict[str, List[Dict]]:
        """Assign recipes to days/slots, respecting variety and cook time.

        Args:
            recipes: List of recipe dicts with cook_time_min, meal_type, id
            meal_type_preferences: e.g. {"monday_dinner": "chicken stir fry"}

        Returns:
            Dict mapping day -> list of assigned meal dicts
        """
        self._plan = {d: [] for d in self.DAYS}
        used_ids = set()
        prefs = meal_type_preferences or {}

        # Fill explicit preferences first
        for day_slot, recipe_id in prefs.items():
            parts = day_slot.rsplit("_", 1)
            if len(parts) != 2:
                continue
            day, meal_type = parts[0].lower(), parts[1]
            slot = next(
                (s for s in self.slots if s.day == day
                 and s.label.endswith(meal_type)),
                None
            )
            if not slot:
                continue
            recipe = next((r for r in recipes if r.get("id") == recipe_id), None)
            if recipe and recipe_id not in used_ids:
                if self.fit_meal_to_slot(recipe, slot):
                    self._plan[day].append(recipe)
                    used_ids.add(recipe_id)

        # Fill remaining slots with best-fit recipes
        last_id = None
        for slot in self.slots:
            day = slot.day
            if len(self._plan[day]) >= 3:
                continue  # max 3 meals per day
            candidates = [
                r for r in recipes
                if r.get("id") not in used_ids
                and r.get("id") != last_id
                and self.fit_meal_to_slot(r, slot)
            ]
            if not candidates:
                candidates = [
                    r for r in recipes
                    if r.get("id") not in used_ids
                    and self.fit_meal_to_slot(r, slot)
                ]
            if candidates:
                chosen = candidates[0]
                self._plan[day].append(chosen)
                used_ids.add(chosen.get("id"))
                last_id = chosen.get("id")

        return self._plan

    def get_plan_summary(self) -> List[Dict]:
        """Return a human-readable plan."""
        summary = []
        for day in self.DAYS:
            meals = self._plan.get(day, [])
            if meals:
                summary.append({
                    "day": day.capitalize(),
                    "meals": [m.get("name", m.get("id", "?")) for m in meals],
                    "count": len(meals),
                })
        return summary