"""RoutineSmith — CLI Entry Point.

Usage:
  routinesmith                   Interactive mode (collect schedule + goals)
  routinesmith --quick           Demo mode (defaults + demo goals)
  routinesmith --report          Generate daily report from last run
"""

import sys
import json
import os
from datetime import date

from .orchestrator import RoutineSmithOrchestrator


REPORT_FILE = None  # Will be set in interactive mode


def main():
    global REPORT_FILE
    args = sys.argv[1:]

    orchestrator = RoutineSmithOrchestrator()
    quick_mode = "--quick" in args
    report_mode = "--report" in args

    if report_mode:
        # Load last report
        last_report = os.path.join(os.path.dirname(__file__), "last_routine.json")
        if os.path.exists(last_report):
            with open(last_report) as f:
                data = json.load(f)
            print(f"\n  Last Routine Report ({data.get('date', 'unknown')}):")
            print(f"  Score: {data.get('score', 'N/A')}/100")
            print(f"  Tasks: {data.get('task_count', 0)}")
            print(f"  Time Used: {data.get('time_used', 0)} minutes")
            print(f"  Vetoes: {data.get('vetoes', 0)}")
            print(f"  Adjustments: {data.get('adjustments', 0)}")
        else:
            print("  No previous routine found. Run 'routinesmith' first.")
        return

    # Full pipeline
    routine = orchestrator.run_full_pipeline(quick_mode=quick_mode)

    # Show the routine
    orchestrator.show_routine(routine)

    # Show negotiation log
    show_log = input("  Show agent negotiation log? (y/N): ").strip().lower()
    if show_log == "y":
        orchestrator.show_negotiation_log()

    # Offer implementation intentions
    print("\n  💡 Tip: Say these aloud every morning for the first week:")
    for task in routine.tasks[:3]:
        if task.cue_trigger:
            print(f"     \"When {task.cue_trigger}, I will {task.label}.\"")
        else:
            print(f"     \"At {task.start_time.strftime('%H:%M')}, I will {task.label}.\"")

    # Save report
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_routine.json")
    with open(report_path, "w") as f:
        json.dump({
            "date": routine.date,
            "score": round(routine.score, 1),
            "task_count": len(routine.tasks),
            "time_used": routine.total_used_minutes,
            "time_available": routine.total_available_minutes,
            "vetoes": len(orchestrator.vetoes),
            "adjustments": len(orchestrator.adjustments),
        }, f, indent=2)

    print(f"  📁 Report saved to last_routine.json")
    print()


if __name__ == "__main__":
    main()