#!/usr/bin/env python3
"""Parallel Lives — CLI tool for simulated voice calls with history's greatest minds.

Usage:
    python main.py --call        # Interactive character call
    python main.py --simulate    # Quick simulated conversation with random character
    python main.py --list        # List available characters
"""

from __future__ import annotations

import os
import random
import sys
from typing import Optional

from dotenv import load_dotenv

from src.characters import get_character, list_characters
from src.conversation import Conversation
from src.responder import generate_response


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def print_header() -> None:
    """Print the app banner."""
    print()
    print("╔══════════════════════════════════════════╗")
    print("║         PARALLEL LIVES    🎭             ║")
    print("║  Simulated voice calls with history's    ║")
    print("║  greatest minds — across time itself.    ║")
    print("╚══════════════════════════════════════════╝")
    print()


def pick_character_interactive() -> Optional[str]:
    """Let the user pick a character from the roster."""
    roster = list_characters()

    print("Who would you like to call?\n")
    for i, (key, char) in enumerate(roster, 1):
        print(f"  {i}. {char.emoji} {char.name} ({char.period})")
    print(f"  {len(roster) + 1}. Surprise me!")
    print()

    raw = input("Enter a number or name: ").strip()
    print()

    # Try number first
    try:
        idx = int(raw) - 1
        if 0 <= idx < len(roster):
            key, char = roster[idx]
            return key
        elif idx == len(roster):
            key, char = random.choice(roster)
            print(f"  → You get: {char.emoji} {char.name}\n")
            return key
    except ValueError:
        pass

    # Try name match
    char = get_character(raw)
    if char:
        return raw.lower().strip()

    # Try partial match by first name
    lower_raw = raw.lower()
    for key, char in roster:
        if lower_raw in key or lower_raw in char.name.lower():
            return key

    print(f"  ❌ '{raw}' not found. Try einstein, cleopatra, holmes, lovelace, joan, socrates.")
    return None


def run_conversation(character_key: str, simulate: bool = True) -> None:
    """Run an interactive conversation with the chosen character."""
    char = get_character(character_key)
    if not char:
        print(f"  ❌ Character '{character_key}' not found.")
        return

    api_key: Optional[str] = None
    if not simulate:
        api_key = os.getenv("LLM_API_KEY")

    conv = Conversation(char)
    greeting = conv.start()

    print(f"\n  📞 Calling {char.emoji} {char.name} ({char.period})...\n")
    print(f"  {char.emoji}  {greeting.content}\n")

    if simulate:
        print("  [Simulated mode — responses are templated]")
    else:
        print("  [Live mode — LLM-generated responses]")
    print()

    while True:
        try:
            user_input = input("  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  📞 Call ended.")
            break

        if not user_input:
            continue

        # Exit words
        if user_input.lower() in ("quit", "exit", "goodbye", "hang up"):
            farewells = [
                f"{char.catchphrase}",
                f"Until we speak again, seeker.",
                f"*a knowing nod* The conversation continues — but elsewhere.",
                f"Farewell. I have enjoyed your company.",
            ]
            print(f"\n  {char.emoji}  {random.choice(farewells)}\n")
            print("  📞 Call ended.\n")
            break

        conv.add_user_turn(user_input)
        response = generate_response(conv, simulate=simulate, api_key=api_key)
        conv.add_character_turn(response)

        # Extract key facts (simple heuristic: track the user's name if they share it)
        name_indicators = ["i am ", "my name is ", "call me ", "i'm "]
        for indicator in name_indicators:
            if indicator in user_input.lower():
                # Extract name — crude but works for MVP
                idx = user_input.lower().index(indicator) + len(indicator)
                name_part = user_input[idx:].strip().split()[0].strip(".,!?")
                if name_part:
                    fact = f"{char.name} knows this caller as {name_part}."
                    conv.add_key_fact(fact)
                    break

        print(f"  {char.emoji}  {response}\n")


def run_simulate(character_key: Optional[str] = None) -> None:
    """Quick simulated demonstration — no interactive input needed."""
    if character_key:
        char = get_character(character_key)
    else:
        key, char = random.choice(list_characters())

    if not char:
        print(f"  ❌ Character not found.")
        return

    conv = Conversation(char)
    greeting = conv.start()

    print(f"\n  📞 Calling {char.emoji} {char.name} ({char.period})...\n")
    print(f"  {char.emoji}  {greeting.content}\n")

    # Simulate a short conversation with predefined prompts
    user_prompts = [
        "Good day! I'm delighted to speak with you.",
        "What do you consider your greatest achievement?",
        "What do you think of the world today?",
    ]

    for prompt in user_prompts:
        print(f"  You: {prompt}")
        conv.add_user_turn(prompt)
        response = generate_response(conv, simulate=True)
        conv.add_character_turn(response)
        print(f"  {char.emoji}  {response}\n")

    print(f"  {char.emoji}  {char.catchphrase}")
    print("\n  📞 Call ended.\n")


def list_roster() -> None:
    """Print all available characters."""
    roster = list_characters()
    print("\n  Available characters:\n")
    for key, char in roster:
        print(f"  {char.emoji}  {char.name}")
        print(f"      Period : {char.period}")
        print(f"      Style  : {char.personality[:80]}...")
        print()


def main() -> int:
    load_dotenv()
    print_header()

    args = sys.argv[1:]

    if "--list" in args or "-l" in args:
        list_roster()
        return 0

    if "--call" in args or "-c" in args:
        # Extract character key if provided after --call
        character_arg: Optional[str] = None
        for i, arg in enumerate(args):
            if arg in ("--call", "-c") and i + 1 < len(args) and not args[i + 1].startswith("--"):
                character_arg = args[i + 1]
                break
        if character_arg:
            run_conversation(character_arg, simulate=True)
        else:
            key = pick_character_interactive()
            if key:
                run_conversation(key, simulate=True)
        return 0

    if "--simulate" in args or "-s" in args:
        character_arg = None
        for i, arg in enumerate(args):
            if arg in ("--simulate", "-s") and i + 1 < len(args) and not args[i + 1].startswith("--"):
                character_arg = args[i + 1]
                break
        run_simulate(character_arg)
        return 0

    # Default: show usage
    print("Usage:")
    print("  python main.py --call        # Interactive character call")
    print("  python main.py --simulate    # Quick demo conversation")
    print("  python main.py --list        # Show available characters")
    print()
    return 1


if __name__ == "__main__":
    sys.exit(main())