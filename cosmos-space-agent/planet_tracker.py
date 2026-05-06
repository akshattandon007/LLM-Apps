#!/usr/bin/env python3
"""
planet_tracker.py — Track any planet with live data + orbital milestones.

Usage:
    python scripts/planet_tracker.py <planet>
    python scripts/planet_tracker.py mars
    python scripts/planet_tracker.py jupiter --facts
    python scripts/planet_tracker.py all
"""

import os
import sys
import argparse
import anthropic

PLANET_TRACKER_SYSTEM = """You are an expert planetary scientist and mission tracker with access to the latest data.

When asked about a planet, provide a structured report with these sections:

🌍 BASIC PROFILE
- Type, diameter, mass, orbital period, distance from Sun (current + range)
- Number of moons, ring system status

📡 ACTIVE MISSIONS (right now)
- Every spacecraft currently orbiting or operating near/on this planet
- Mission agency, launch date, current status, key recent discoveries

🚀 UPCOMING MISSIONS
- All confirmed future missions targeting this planet (next 5 years)
- Launch windows, agencies, objectives

🏆 TRACKING MILESTONES
- Top 10 most astonishing facts discovered in the last 2 years
- Recent orbital anomalies, atmospheric events, geological activity
- Record-breaking measurements (closest approach, highest resolution image, etc.)

🔭 VISIBILITY & OBSERVATION
- Current sky position (constellation, magnitude if visible)
- Next best viewing opportunity for amateur astronomers

Always search for the most current mission status data. Be precise with dates and figures.
Use vivid descriptions that convey the alien wonder of this world.
"""


def track_planet(planet_name: str, client: anthropic.Anthropic, extra_facts: bool = False) -> str:
    """Query the agent for comprehensive planet tracking data."""

    query = f"Give me a full tracking report for {planet_name}. Include current missions, upcoming missions, orbital milestones, and the most amazing recent discoveries. Search for the very latest 2024-2025 data."

    if extra_facts:
        query += " Also include 5 mind-blowing historical discoveries that changed our understanding of this planet."

    tools = [{"type": "web_search_20250305", "name": "web_search"}]

    messages = [{"role": "user", "content": query}]

    print(f"\n🔭 Scanning telemetry for {planet_name.title()}...\n")

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        system=PLANET_TRACKER_SYSTEM,
        tools=tools,
        messages=messages,
    )

    # Handle tool use loop
    while response.stop_reason == "tool_use":
        tool_results = []
        for block in response.content:
            if hasattr(block, "type") and block.type == "tool_use":
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": "Search completed.",
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            system=PLANET_TRACKER_SYSTEM,
            tools=tools,
            messages=messages,
        )

    # Extract text
    result = ""
    for block in response.content:
        if hasattr(block, "type") and block.type == "text":
            result += block.text

    return result


def track_all_planets(client: anthropic.Anthropic) -> str:
    """Get a solar system-wide mission overview."""

    query = """Give me a current solar system mission status overview. 
    For each planet (Mercury through Neptune) plus dwarf planets, list:
    - Any active spacecraft/missions
    - Most exciting recent discovery (2024-2025)
    - Any upcoming missions in next 2 years
    Format as a quick-scan dashboard."""

    tools = [{"type": "web_search_20250305", "name": "web_search"}]
    messages = [{"role": "user", "content": query}]

    print("\n🌌 Scanning the entire solar system...\n")

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=6000,
        system=PLANET_TRACKER_SYSTEM,
        tools=tools,
        messages=messages,
    )

    while response.stop_reason == "tool_use":
        tool_results = []
        for block in response.content:
            if hasattr(block, "type") and block.type == "tool_use":
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": "Search completed.",
                })
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=6000,
            system=PLANET_TRACKER_SYSTEM,
            tools=tools,
            messages=messages,
        )

    result = ""
    for block in response.content:
        if hasattr(block, "type") and block.type == "text":
            result += block.text

    return result


VALID_PLANETS = {
    "mercury", "venus", "earth", "mars", "jupiter",
    "saturn", "uranus", "neptune", "pluto", "all"
}


def main():
    parser = argparse.ArgumentParser(
        description="🚀 COSMOS Planet Tracker — Real-time planetary intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/planet_tracker.py mars
  python scripts/planet_tracker.py jupiter --facts
  python scripts/planet_tracker.py saturn
  python scripts/planet_tracker.py all
        """,
    )
    parser.add_argument(
        "planet",
        help=f"Planet name or 'all'. Valid: {', '.join(sorted(VALID_PLANETS))}",
    )
    parser.add_argument(
        "--facts",
        action="store_true",
        help="Include additional historical discovery facts",
    )

    args = parser.parse_args()
    planet = args.planet.lower().strip()

    if planet not in VALID_PLANETS:
        print(f"❌ Unknown planet: '{planet}'")
        print(f"   Valid options: {', '.join(sorted(VALID_PLANETS))}")
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not set.")
        print("   Export it: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("\n" + "═" * 60)
    print(f"  🪐  COSMOS Planet Tracker")
    print(f"  Target: {planet.title()}")
    print("═" * 60)

    try:
        if planet == "all":
            result = track_all_planets(client)
        else:
            result = track_planet(planet, client, extra_facts=args.facts)

        print(result)
        print("\n" + "═" * 60)
        print("  Data sourced live via Claude + Web Search")
        print("═" * 60 + "\n")

    except anthropic.APIError as e:
        print(f"❌ API Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n🌠 Tracking aborted.")
        sys.exit(0)


if __name__ == "__main__":
    main()
