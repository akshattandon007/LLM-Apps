# ⏰ RoutineSmith — Daily Routine Optimizer & Habit Architect

> **5 specialized AI agents collaborate to design your ideal daily routine. Tell them your schedule and goals — they negotiate, veto, and optimize until you get a personalized minute-by-minute plan.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/akshattandon007/LLM-Apps)

---

## 🧠 What It Does

**RoutineSmith** is a multi-agent system that builds a daily routine from scratch:

- **⏰ Time Auditor** — Maps your schedule, finds every free minute
- **🎯 Goal Aligner** — Translates "I want to exercise more" into concrete daily tasks
- **🧱 Habit Architect** — Stacks new habits onto existing cues using behavioral psychology (Atomic Habits, Tiny Habits, The Power of Habit)
- **⚡ Energy Matcher** — Places tasks in energy-optimal windows based on your chronotype
- **🕯️ Wind-Down Planner** — Designs your evening shutdown routine for better sleep

The agents **negotiate with each other** — the Energy Matcher can veto the Habit Architect's placement, and the Time Auditor tells the Goal Aligner when goals exceed capacity.

---

## 🚀 Quick Start

```bash
# Clone the repo and navigate
cd LLM-Apps/advanced-ai-agents/routine-smith/

# Install (no deps needed — pure Python stdlib)
pip install -e .

# Run in interactive mode
routinesmith
```

### Demo Mode (one command, no input)

```bash
routinesmith --quick
```

This uses default schedule (7 AM wake, 9-5 work) and 5 demo goals to show you how it works.

### View Last Report

```bash
routinesmith --report
```

---

## 💡 Example

```
$ routinesmith --quick

========================================================
  RoutineSmith — Your Daily Routine Architect
  ⏰ Time Auditor | 🎯 Goal Aligner | 🧱 Habit Architect
  ⚡ Energy Matcher | 🕯️ Wind-Down Planner
========================================================

  ⏰ Time Auditor: Found 4 time pockets (465 free minutes)
  🎯 Goal Aligner: 5 goals → 8 tasks
  🧱 Habit Architect: 5 habit stacks designed
  ⚡ Energy Matcher: 8 tasks placed in optimal energy windows
  🕯️ Wind-Down Planner: 4 wind-down activities

──────────────────────────────────────────────────
 🌅 Your Daily Routine — 2026-11-20
──────────────────────────────────────────────────

 ⏰ 6:00 AM
   💪 06:30 — Exercise for 20 minutes (20min) 🔗 (after morning coffee)

 ⏰ 8:00 AM
   📚 08:00 — Clean inbox for 5 minutes (5min) 🔗 (after sitting down at desk)

 ⏰ 12:00 PM
   🧘 12:00 — Meditate for 10 minutes (10min) 🔗 (after brushing teeth in morning)

 ⏰ 5:00 PM
   🎨 17:30 — Work on side project (45min)

 ⏰ 9:30 PM
   😴 21:30 — Screen-free wind-down (30min)
   📋 22:10 — Prepare for tomorrow (5min)
   🧘 22:20 — Reflection: 3 good things (5min)
   📚 22:30 — Read a few pages (10min)

──────────────────────────────────────────────────
 📊 Score: 78/100
 ⏱  150 min used of 465 min available (32% utilization)
```

---

## 🏗️ Architecture

```
CLI (cli.py)
  └── Orchestrator (orchestrator.py)
        ├── Time Auditor → agents/time_auditor.py
        ├── Goal Aligner  → agents/goal_aligner.py
        ├── Habit Architect → agents/habit_architect.py
        ├── Energy Matcher → agents/energy_matcher.py
        └── Wind-Down Planner → agents/wind_down_planner.py
```

Each agent is a self-contained class with a single responsibility. Agents communicate through `AgentMessage` objects logged by the orchestrator, which tracks every proposal, veto, and adjustment.

---

## 🧪 Running Tests

```bash
cd advanced-ai-agents/routine-smith/
pip install pytest
python -m pytest routine_smith/tests/ -v
```

---

## 📁 Project Structure

```
routine-smith/
├── requirements.txt         # Dependencies (pytest only)
├── pyproject.toml           # Project config
├── routine_smith/           # Main package
│   ├── __init__.py          # Package init
│   ├── cli.py               # CLI entry point
│   ├── models.py            # Shared data models
│   ├── orchestrator.py      # Main orchestrator (multi-agent coordinator)
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── time_auditor.py      # Schedule analysis agent
│   │   ├── goal_aligner.py      # Goal→task translation agent
│   │   ├── habit_architect.py   # Behavioral design agent
│   │   ├── energy_matcher.py    # Chronotype-aware placement agent
│   │   └── wind_down_planner.py # Evening routine agent
│   ├── data/
│   │   ├── __init__.py
│   │   ├── energy_curves.py     # Chronotype energy curves
│   │   ├── habit_rules.py       # Habit formation rules
│   │   └── time_estimates.py    # Activity duration estimates
│   └── tests/
│       ├── __init__.py
│       └── test_all.py          # 15 tests covering models, agents, energy curves
├── README.md                # ← You are here
├── Decisions.md             # Architecture decisions
└── Flow.md                  # Execution flow documentation
```

---

## 📄 License

MIT — free to use, modify, and share.