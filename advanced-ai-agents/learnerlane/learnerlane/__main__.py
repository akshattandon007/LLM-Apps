#!/usr/bin/env python3
"""
LearnerLane — Multi-Agent Learning Curriculum Builder

Tell us what you want to learn, and LearnerLane builds a complete learning plan:
curriculum modules, free resources, and weekly practice exercises.

Usage:
  python -m learnerlane                      # Interactive mode (prompt for input)
  python -m learnerlane "photography"         # Quick: topic only
  python -m learnerlane "photography" --demo  # Demo mode (simulated, no API calls)
  python -m learnerlane --demo                # Run the built-in demo
"""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="LearnerLane — Multi-Agent Learning Curriculum Builder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m learnerlane
      Interactive mode: you'll be asked what you want to learn

  python -m learnerlane "photography"
      Build a learning plan for photography

  python -m learnerlane "guitar" --demo
      Run in demo mode (no API calls, built-in templates)

  python -m learnerlane --demo
      Run the built-in demo showing all features
        """
    )
    parser.add_argument("topic", nargs="?", help="What do you want to learn?")
    parser.add_argument("--level", default="beginner", choices=["beginner", "dabbler", "intermediate"],
                        help="Your current skill level (default: beginner)")
    parser.add_argument("--time", default="1-3 hours/week",
                        choices=["<1 hour/week", "1-3 hours/week", "3-5 hours/week", "5+ hours/week"],
                        help="Time commitment per week")
    parser.add_argument("--goal", help="Your learning goal (free-form)")
    parser.add_argument("--demo", action="store_true", help="Run demo mode with built-in examples")
    
    args = parser.parse_args()
    
    # ── Demo mode ────────────────────────────────────────────────────────
    if args.demo:
        demo_topics = [
            ("photography", "beginner", "2-3 hours/week", "I want to learn photography to take better travel photos"),
            ("guitar", "beginner", "1-3 hours/week", "Always wanted to play guitar"),
            ("python", "dabbler", "3-5 hours/week", "Learn Python for data analysis"),
        ]
        from learnerlane.orchestrator import run_pipeline, format_plan
        for topic, level, time, goal in demo_topics:
            print(f"\n\n{'#'*70}")
            print(f"#  DEMO: {topic.upper()}")
            print(f"{'#'*70}\n")
            plan = run_pipeline(topic=topic, level=level, time_per_week=time, goal=goal, mode="simulated")
            print(format_plan(plan))
            print("\n" + "=" * 70)
        return
    
    # ── Quick mode (topic specified) ─────────────────────────────────────
    if args.topic:
        from learnerlane.orchestrator import run_pipeline, format_plan
        plan = run_pipeline(
            topic=args.topic,
            level=args.level,
            time_per_week=args.time,
            goal=args.goal or f"I want to learn {args.topic}",
            mode="simulated",
        )
        print(format_plan(plan))
        return
    
    # ── Interactive mode ─────────────────────────────────────────────────
    print("📚  LEARNERLANE — Learning Curriculum Builder")
    print("=" * 60)
    print("Tell me what you want to learn, and I'll build you a complete plan.")
    print()
    
    topic = input("What skill or topic do you want to learn? ").strip()
    if not topic:
        print("No topic given. Running demo instead...")
        # Run demo
        from learnerlane.orchestrator import run_pipeline, format_plan
        plan = run_pipeline(topic="photography", level="beginner", time_per_week="1-3 hours/week",
                           goal="Learn photography", mode="simulated")
        print(format_plan(plan))
        return
    
    print()
    print(f"Great! Let me build a learning plan for '{topic}'...")
    print()
    
    from learnerlane.orchestrator import run_pipeline, format_plan
    plan = run_pipeline(
        topic=topic,
        level=args.level,
        time_per_week=args.time,
        goal=args.goal or f"I want to learn {topic}",
        mode="simulated",
    )
    print(format_plan(plan))


if __name__ == "__main__":
    main()