"""
Space Fact Agent - Powered by Claude with web search
Interacts with NASA, ESA, SpaceX, and other space sources
"""

import os
import json
import anthropic
from typing import Optional


SYSTEM_PROMPT = """You are COSMOS — a highly intelligent Space Intelligence Agent powered by real-time data.

Your mission: deliver cutting-edge, accurate, and awe-inspiring space news and research from:
- NASA (nasa.gov, jpl.nasa.gov, apod.nasa.gov)
- ESA (esa.int)
- SpaceX (spacex.com)
- JAXA (jaxa.jp)
- ISRO (isro.gov.in)
- Roscosmos
- China National Space Administration (CNSA)
- arXiv space/astrophysics preprints
- Sky & Telescope, Space.com, The Planetary Society

Behavior rules:
1. Always search the web for the LATEST information before answering
2. Cite your sources clearly (agency or publication name)
3. Use vivid, human language — make space feel visceral and real
4. For upcoming events, include precise dates and times (UTC) when available
5. For planetary tracking questions, give orbital mechanics, recent missions, and spectacular facts
6. Maintain conversation context across follow-up queries
7. When uncertain, say so — never hallucinate mission data or orbital figures
8. Format responses with clear sections using emoji headers for readability

You speak with the authority of a veteran mission controller and the wonder of a child seeing the stars for the first time.
"""


def create_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return anthropic.Anthropic(api_key=api_key)


def run_agent(
    user_message: str,
    conversation_history: list,
    client: anthropic.Anthropic,
) -> tuple[str, list]:
    """
    Run one turn of the space agent, returning (response_text, updated_history).
    Uses extended thinking + web search tool for accuracy.
    """

    conversation_history.append({"role": "user", "content": user_message})

    tools = [
        {
            "type": "web_search_20250305",
            "name": "web_search",
        }
    ]

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=tools,
        messages=conversation_history,
    )

    # Collect full assistant response including tool use blocks
    assistant_content = response.content

    # Extract text from response
    response_text = ""
    for block in assistant_content:
        if hasattr(block, "type") and block.type == "text":
            response_text += block.text

    # Append assistant turn to history
    conversation_history.append({"role": "assistant", "content": assistant_content})

    # Handle tool use (web search) - Claude handles this automatically with web_search tool
    # If stop_reason is tool_use, we need to continue the loop
    while response.stop_reason == "tool_use":
        # Build tool results
        tool_results = []
        for block in assistant_content:
            if hasattr(block, "type") and block.type == "tool_use":
                # The web_search tool returns results automatically; we just pass them back
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "Search completed.",
                    }
                )

        if not tool_results:
            break

        conversation_history.append({"role": "user", "content": tool_results})

        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=conversation_history,
        )

        assistant_content = response.content
        response_text = ""
        for block in assistant_content:
            if hasattr(block, "type") and block.type == "text":
                response_text += block.text

        conversation_history.append({"role": "assistant", "content": assistant_content})

    return response_text, conversation_history


def chat_loop():
    """Interactive chat loop for the space agent."""
    client = create_client()
    conversation_history = []

    print("\n" + "═" * 60)
    print("  🚀  COSMOS — Space Intelligence Agent  🌌")
    print("  Powered by Claude + Real-Time Web Search")
    print("═" * 60)
    print("Ask about latest space news, missions, or planets.")
    print("Type 'exit' or 'quit' to leave.\n")

    while True:
        try:
            user_input = input("You › ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n🌠 Safe travels, explorer. Ad astra!")
            break

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit", "q"}:
            print("\n🌠 Safe travels, explorer. Ad astra!")
            break

        print("\nCOSMOS › Searching the cosmos...\n")

        try:
            response_text, conversation_history = run_agent(
                user_input, conversation_history, client
            )
            print(f"COSMOS › {response_text}\n")
            print("─" * 60 + "\n")
        except anthropic.APIError as e:
            print(f"[API Error] {e}\n")
        except Exception as e:
            print(f"[Error] {e}\n")


if __name__ == "__main__":
    chat_loop()
