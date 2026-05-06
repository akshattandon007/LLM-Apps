"""
launch_tracker.py — Track upcoming rocket launches worldwide.
"""

import os
import anthropic

LAUNCH_SYSTEM = """You are a rocket launch tracking specialist. Search for upcoming and recent rocket launches worldwide.

For each launch provide:
🚀 MISSION NAME
├─ Vehicle: [Rocket name]
├─ Agency/Company: [Who's launching]
├─ Launch Site: [Location]
├─ Date/Window: [UTC datetime or window]
├─ Payload: [What's being carried]
├─ Orbit/Destination: [Where it's going]
└─ Status: [Confirmed / NET / Scrubbed / Success / Failure]

Search for real-time launch data. Be precise with dates.
"""


def get_upcoming_launches(count: int = 10, client: anthropic.Anthropic = None) -> str:
    if client is None:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    query = f"Search for the next {count} upcoming rocket launches worldwide. Include SpaceX, NASA, ESA, Roscosmos, ISRO, JAXA, and commercial providers. Include launch windows in UTC."

    tools = [{"type": "web_search_20250305", "name": "web_search"}]
    messages = [{"role": "user", "content": query}]

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=3000,
        system=LAUNCH_SYSTEM,
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
            max_tokens=3000,
            system=LAUNCH_SYSTEM,
            tools=tools,
            messages=messages,
        )

    result = ""
    for block in response.content:
        if hasattr(block, "type") and block.type == "text":
            result += block.text

    return result


if __name__ == "__main__":
    import sys
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    print(f"\n🚀 Upcoming Launches (next {count})\n" + "═" * 50)
    print(get_upcoming_launches(count))
