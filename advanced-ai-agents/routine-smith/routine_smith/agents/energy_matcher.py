"""Energy Matcher Agent — Assigns tasks to energy-appropriate time slots.

Responsibilities:
- Map user's chronotype to energy curve
- Check if proposed task placements match energy profile
- Veto/go tasks based on energy compatibility
- Suggest optimal timing for each task
"""

from datetime import time
from typing import Optional

from ..models import (
    UserProfile, RoutineTask, TaskEnergyLevel, AgentMessage, TimePocket,
    EnergyPattern,
)
from ..data.energy_curves import (
    get_energy_at_hour, is_task_compatible, Chronotype, ENERGY_CURVES,
)


class EnergyMatcher:
    """Matches tasks to appropriate energy windows based on chronotype."""

    def __init__(self):
        self.name = "Energy Matcher"

    def _to_chronotype(self, pattern: EnergyPattern) -> Chronotype:
        mapping = {
            EnergyPattern.MORNING: Chronotype.MORNING,
            EnergyPattern.NIGHT: Chronotype.NIGHT,
            EnergyPattern.BALANCED: Chronotype.BALANCED,
        }
        return mapping.get(pattern, Chronotype.BALANCED)

    def evaluate_placement(self, task: RoutineTask, pocket: TimePocket,
                           profile: UserProfile) -> tuple[bool, Optional[str]]:
        """Evaluate if a task placement is energy-compatible. Returns (pass, reason)."""
        chronotype = self._to_chronotype(profile.energy_pattern)
        hour = task.start_time.hour

        compatible = is_task_compatible(chronotype, hour, task.energy_level.value)

        if compatible:
            return True, None

        energy = get_energy_at_hour(chronotype, hour)
        return False, (
            f"Energy level at {task.start_time.strftime('%H:%M')} is {energy}/10, "
            f"but '{task.label}' requires {task.energy_level.value.upper()} energy "
            f"({TaskEnergyLevel(task.energy_level).value}). "
            f"Recommended hours: {self._recommend_hours(chronotype, task.energy_level.value)}."
        )

    def _recommend_hours(self, chronotype: Chronotype, energy_label: str) -> str:
        """Get human-readable recommended hours for a task type."""
        from ..data.energy_curves import best_hours_for_task
        hours = best_hours_for_task(chronotype, energy_label)
        if not hours:
            return "any consistent time"

        # Group consecutive hours
        ranges = []
        start = hours[0]
        end = hours[0]
        for h in hours[1:]:
            if h == end + 1:
                end = h
            else:
                ranges.append(f"{start:02d}:00-{end + 1:02d}:00" if start != end else f"{start:02d}:00")
                start = h
                end = h
        ranges.append(f"{start:02d}:00-{end + 1:02d}:00" if start != end else f"{start:02d}:00")
        return ", ".join(ranges)

    def select_best_pocket(self, task: RoutineTask, pockets: list[TimePocket],
                           profile: UserProfile) -> tuple[Optional[TimePocket], Optional[str]]:
        """Select the best time pocket for a task based on energy compatibility."""
        chronotype = self._to_chronotype(profile.energy_pattern)
        required_label = task.energy_level.value

        scored_pockets = []
        for pocket in pockets:
            if pocket.duration_minutes < task.duration_minutes:
                continue

            mid_hour = (pocket.start.hour + pocket.end.hour) // 2
            energy = get_energy_at_hour(chronotype, mid_hour)

            # Score: higher energy match = better, but don't overshoot too much
            if required_label == "high":
                score = energy if energy >= 7 else energy * 0.3
            elif required_label == "low":
                score = (10 - energy) if energy <= 5 else (10 - energy) * 0.3
            else:  # medium
                score = 10 - abs(energy - 5)

            if task.is_habit_stack and pocket.is_mealtime_linked:
                score *= 0.5  # Mealtime isn't ideal for habit stacking

            scored_pockets.append((score, pocket))

        if not scored_pockets:
            # Fallback: any pocket big enough
            big_enough = [p for p in pockets if p.duration_minutes >= task.duration_minutes]
            if big_enough:
                return max(big_enough, key=lambda p: p.duration_minutes), f"Fallback: {big_enough[0].label}"
            return None, "No pocket large enough for this task."

        scored_pockets.sort(key=lambda x: x[0], reverse=True)
        best = scored_pockets[0]
        return best[1], f"Energy score: {best[0]:.1f}/10 in '{best[1].label}'"

    def match_all_tasks(self, tasks: list[RoutineTask], pockets: list[TimePocket],
                        profile: UserProfile) -> tuple[list[RoutineTask], list[AgentMessage]]:
        """Match all tasks to optimal time pockets by energy compatibility."""
        matched: list[RoutineTask] = []
        messages: list[AgentMessage] = []
        used_pockets = set()

        # Sort tasks: high-energy first (most constrained), then low-energy
        sorted_tasks = sorted(tasks, key=lambda t: (
            0 if t.energy_level == TaskEnergyLevel.HIGH else
            1 if t.energy_level == TaskEnergyLevel.LOW else 2
        ))

        for task in sorted_tasks:
            # Try to find the best pocket
            available_pockets = [p for p in pockets if p.label not in used_pockets
                                  or sum(1 for t in matched if t.notes and p.label in t.notes) < 2]

            best_pocket, reason = self.select_best_pocket(task, available_pockets or pockets, profile)

            if best_pocket:
                task.start_time = best_pocket.start
                existing_note = task.notes
                task.notes = f"{existing_note} | Energy-placed: {reason}"
                used_pockets.add(best_pocket.label)
                matched.append(task)
                messages.append(AgentMessage(
                    sender="Energy Matcher",
                    recipient="orchestrator",
                    message_type="proposal",
                    content=f"Placed '{task.label}' in '{best_pocket.label}' ({best_pocket.start.strftime('%H:%M')}). "
                            f"{reason}.",
                ))
            else:
                # Task couldn't be placed — report veto
                messages.append(AgentMessage(
                    sender="Energy Matcher",
                    recipient="orchestrator",
                    message_type="veto",
                    content=f"Could not place '{task.label}' ({task.duration_minutes}min, "
                            f"{task.energy_level.value}). {reason}",
                ))

        # Check for energy conflicts in matched tasks
        chronotype = self._to_chronotype(profile.energy_pattern)
        for task in matched:
            hour = task.start_time.hour
            compatible = is_task_compatible(chronotype, hour, task.energy_level.value)
            if not compatible:
                messages.append(AgentMessage(
                    sender="Energy Matcher",
                    recipient="Habit Architect",
                    message_type="veto",
                    content=f"VETO: '{task.label}' at {task.start_time.strftime('%H:%M')} — "
                            f"energy mismatch! Your energy at that time is "
                            f"{get_energy_at_hour(chronotype, hour)}/10, "
                            f"but this task needs {task.energy_level.value.upper()}.",
                ))

        messages.append(AgentMessage(
            sender="Energy Matcher",
            recipient="orchestrator",
            message_type="info",
            content=f"Matched {len(matched)}/{len(tasks)} tasks to optimal time slots. "
                    f"Energy compatibility optimized for {profile.energy_pattern.value} chronotype.",
        ))

        return matched, messages