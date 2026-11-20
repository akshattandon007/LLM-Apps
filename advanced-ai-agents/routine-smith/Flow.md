# Flow.md — RoutineSmith Execution Flow

## Overview

RoutineSmith uses a 5-agent pipeline orchestrated by `RoutineSmithOrchestrator`. Each agent has a single responsibility and communicates via `AgentMessage` objects. The orchestrator runs agents sequentially, but agents negotiate via messages (the Energy Matcher can veto the Habit Architect's placements; the Time Auditor can flag capacity issues to the Goal Aligner).

---

## Execution Path: Interactive Mode

```
cli.py:main()
  │
  ├── RoutineSmithOrchestrator.__init__()
  │     ├── TimeAuditor.__init__()
  │     ├── GoalAligner.__init__()
  │     ├── HabitArchitect.__init__()
  │     ├── EnergyMatcher.__init__()
  │     └── WindDownPlanner.__init__()
  │
  ├── run_full_pipeline(quick_mode=False)
  │     │
  │     │  STEP 1 — Time Auditor
  │     ├── TimeAuditor.collect_schedule()
  │     │     └── UserProfile creation with user input (or defaults)
  │     ├── TimeAuditor.audit()
  │     │     └── TimeAuditor.find_time_pockets(profile)
  │     │           └── Returns list[TimePocket], list[AgentMessage]
  │     │
  │     │  STEP 2 — Goal Aligner
  │     ├── GoalAligner.collect_goals()
  │     │     └── Returns list[Goal] (user input or demo goals)
  │     ├── GoalAligner.goals_to_tasks(goals, pockets, profile)
  │     │     ├── Sorts goals by urgency (critical → flexible)
  │     │     ├── Scales or drops goals if > available time
  │     │     ├── For each goal: _find_best_pocket()
  │     │     └── Returns list[RoutineTask], list[AgentMessage]
  │     │
  │     │  STEP 3 — Habit Architect
  │     ├── HabitArchitect.identify_cues(profile)
  │     │     └── Returns list[str] of existing daily cues
  │     ├── HabitArchitect.design_habit_stacks(goals, profile, cues)
  │     │     ├── For each goal: find_stacks_for_goal(category)
  │     │     ├── Selects best HabitStack (no cue conflict)
  │     │     ├── Creates RoutineTask with cue_trigger and min_viable_version
  │     │     └── Returns list[RoutineTask], list[AgentMessage]
  │     ├── _merge_habits(tasks, habits)
  │     │     └── Replaces base tasks with their habit-stacked versions
  │     │
  │     │  STEP 4 — Energy Matcher
  │     ├── EnergyMatcher.match_all_tasks(tasks, pockets, profile)
  │     │     ├── Sorts tasks: HIGH energy first (most constrained)
  │     │     ├── For each task:
  │     │     │     ├── select_best_pocket(task, pockets, profile)
  │     │     │     │     ├── Scores each pocket by energy compatibility
  │     │     │     │     └── Returns best TimePocket + reason
  │     │     │     ├── Assigns task.start_time = pocket.start
  │     │     │     └── Checks energy compatibility → veto flag
  │     │     └── Returns list[RoutineTask], list[AgentMessage]
  │     │
  │     │  STEP 5 — Wind-Down Planner
  │     ├── WindDownPlanner.design_wind_down(profile, goals, tasks)
  │     │     ├── Screen-off block (30 min pre-wind-down)
  │     │     ├── Tomorrow prep block (5 min)
  │     │     ├── Gratitude/reflection block (5 min)
  │     │     ├── Reading block (10 min, if learning goals exist)
  │     │     └── Returns list[RoutineTask], list[AgentMessage]
  │     │
  │     │  COMPILE
  │     ├── _merge_habits() — applies habit stacks
  │     ├── _calculate_score(tasks, goals) → 0-100
  │     └── Returns DailyRoutine (sorted tasks, score, vetoes, adjustments)
  │
  ├── show_routine(routine)
  │     ├── Groups tasks by hour
  │     ├── Shows icons, cue triggers, energy notes
  │     └── Shows score, utilization, veto count
  ├── show_negotiation_log() [on request]
  └── Save last_routine.json
```

---

## Execution Path: Quick Mode (`--quick`)

Same as above, except:
- `TimeAuditor.collect_schedule()` → uses `UserProfile()` defaults (7AM wake, 9-5 work, balanced)
- `GoalAligner.collect_goals()` → uses `_demo_goals()` (exercise, read, meditate, side project, stretch)
- No user input required

---

## Execution Path: Report Mode (`--report`)

```
cli.py:main() with --report
  └── Reads last_routine.json from package directory
        └── Prints: date, score, task_count, time_used, vetoes, adjustments
```

---

## Module Dependency Graph

```
routine_smith/
│
├── cli.py ─────────────────────────────┐
│                                       │
├── orchestrator.py ────────────────────┤
│    │  depends on:                     │
│    ├── models.py                      │  ◀── Shared data models
│    ├── agents/time_auditor.py ────────┤
│    ├── agents/goal_aligner.py  ───────┤  │
│    ├── agents/habit_architect.py ─────┤  │  depends on:
│    │    └── data/habit_rules.py       │  │    depends on: (stdlib)
│    ├── agents/energy_matcher.py ──────┤  │    depends on:
│    │    └── data/energy_curves.py     │  │      (stdlib)
│    └── agents/wind_down_planner.py ───┤  │
│                                       │  │
├── models.py ◀─────────────────────────┘  │  Used by ALL agents
│                                          │
├── data/                                  │
│   ├── energy_curves.py ◀── EnergyMatcher │
│   ├── habit_rules.py    ◀── HabitArchitect
│   └── time_estimates.py ◀── (reserved)   │
│                                          │
└── tests/                                 │
    └── test_all.py ◀── tests all modules  │
```

---

## Key Data Flow

```
User Input / Defaults
    │
    ▼
UserProfile (wake_time, sleep_time, commute, work_hours, energy_pattern)
    │
    ▼  (Step 1: Time Auditor)
list[TimePocket] — available time windows with energy labels
    │
    ▼  (Step 2: Goal Aligner)
    │
Goals (user tells us what they want)
    │
    ▼
list[RoutineTask] — concrete tasks with durations and energy requirements
    │
    ▼  (Step 3: Habit Architect)
    │
list[RoutineTask] (tasks replaced by habit-stacked versions with cue triggers)
    │
    ▼  (Step 4: Energy Matcher)
    │
list[RoutineTask] (tasks assigned to specific start_times based on energy curves)
    │
    ▼  (Step 5: Wind-Down Planner)
    │
list[RoutineTask] (wind-down tasks appended: screen-off, prep, reflection, reading)
    │
    ▼
DailyRoutine (sorted by time, with score, vetoes, adjustments)
    │
    ▼
CLI display + last_routine.json
```

---

## Agent Communication Flow

```
Time Auditor ──info──→ Orchestrator: "4 pockets, 465 free min"
    │
    │  Time Auditor ──adjustment──→ Goal Aligner: "Only 60min available!"
    │
    ▼
Goal Aligner ──adjustment──→ Time Auditor: "Reduced goals to fit"
    │
Goal Aligner ──info──→ Orchestrator: "5 goals → 8 tasks"
    │
    ▼
Habit Architect ──proposal──→ Orchestrator: "Stacked exercise on coffee"
    │
    ▼
Energy Matcher ──proposal──→ Orchestrator: "Placed exercise in Morning pocket"
    │
Energy Matcher ──veto──→ Habit Architect: "VETO: energy mismatch at 6AM!"
    │
    ▼
Wind-Down Planner ──proposal──→ Orchestrator: "Screen-off at 9:30PM"
    │
Wind-Down Planner ──info──→ Orchestrator: "Wind-down: 4 activities, 50 min"
```

---

## Function-Level Call Chains

### `cli.py:main()`
```
main()
  └── RoutineSmithOrchestrator.run_full_pipeline(quick)
        ├── TimeAuditor.collect_schedule() → UserProfile
        ├── TimeAuditor.audit() → (pockets, messages)
        │     └── TimeAuditor.find_time_pockets() → list[TimePocket]
        ├── GoalAligner.collect_goals() → list[Goal]
        ├── GoalAligner.goals_to_tasks(goals, pockets, profile) → (tasks, messages)
        │     ├── GoalAligner._find_best_pocket(goal, pockets, profile) → TimePocket|None
        │     └── sorted() + list comprehension
        ├── HabitArchitect.identify_cues(profile) → list[str]
        ├── HabitArchitect.design_habit_stacks(goals, profile, cues) → (habits, messages)
        │     └── data.habit_rules.find_stacks_for_goal(category) → list[HabitStack]
        ├── RoutineSmithOrchestrator._merge_habits(tasks, habits) → list[RoutineTask]
        ├── EnergyMatcher.match_all_tasks(tasks, pockets, profile) → (tasks, messages)
        │     ├── EnergyMatcher.select_best_pocket(task, pockets, profile) → (pocket, reason)
        │     │     └── data.energy_curves.get_energy_at_hour(chronotype, hour) → int
        │     └── data.energy_curves.is_task_compatible(chronotype, hour, label) → bool
        ├── WindDownPlanner.design_wind_down(profile, goals, tasks) → (tasks, messages)
        └── RoutineSmithOrchestrator._calculate_score(tasks, goals) → float
  └── RoutineSmithOrchestrator.show_routine(routine)
  └── RoutineSmithOrchestrator.show_negotiation_log() [on request]
```

### `tests/test_all.py`
```
TestModels.test_user_profile_defaults()
TestModels.test_goal_creation()
TestModels.test_routine_task_creation()
TestModels.test_daily_routine_completion_rate()
TestEnergyCurves.test_get_energy_at_hour()
TestEnergyCurves.test_is_task_compatible()
TestHabitRules.test_find_stacks_for_goal()
TestHabitRules.test_suggest_cue()
TestHabitRules.test_predefined_stacks_have_all_fields()
TestTimeEstimates.test_estimate_duration_known()
TestTimeEstimates.test_estimate_duration_unknown()
TestAgentInteractions.test_goal_to_task_translation()
TestAgentInteractions.test_energy_mismatch_detection()
TestAgentInteractions.test_orchestrator_pipeline_key_components()
TestScoreCalculation.test_score_bounds()
```