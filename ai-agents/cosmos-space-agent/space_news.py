"""
space_news.py — Fetch latest space news from major agencies.
Can be used standalone or imported by the agent.
"""

import os
import anthropic

NEWS_SYSTEM = """You are a space news aggregator. Search for and summarize the latest space news 
from NASA, ESA, SpaceX, JAXA, ISRO, CNSA, and major space publications.

Format each story as:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[EMOJI] HEADLINE
Source: [Agency/Publication] | Date: [Date]
Summary: [2-3 sentences, factual and vivid]
Why it matters: [1 sentence on significance]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Always search for stories from the last 7 days. Return at least 5 stories.
"""


def fetch_latest_news(
    topic: str = "space exploration",
    days: int = 7,
    client: anthropic.Anthropic = None,
) -> str:
    """Fetch latest space news on a given topic."""

    if client is None:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    query = f"Search for the latest {topic} news from the last {days} days. Include stories from NASA, ESA, SpaceX, and major space agencies. Focus on discoveries, launches, and mission updates."

    tools = [{"type": "web_search_20250305", "name": "web_search"}]
    messages = [{"role": "user", "content": query}]

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=3000,
        system=NEWS_SYSTEM,
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
            system=NEWS_SYSTEM,
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
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "space exploration"
    print(f"\n🌐 Fetching latest news: {topic}\n")
    print(fetch_latest_news(topic))
