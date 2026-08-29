#!/usr/bin/env python3
"""Roster — CLI entry point.

Usage:
    python main.py --roast          # Interactive: describe a group and get roasted
    python main.py --simulate       # Run with built-in example groups
    python main.py --tone           # List available tones
    python main.py --help           # Show this message
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from dotenv import load_dotenv

from src.card import CARD_WIDTH, format_card
from src.models import (
    Arrangement,
    Expression,
    GroupPhoto,
    Outfit,
    Person,
    Vibe,
)
from src.roaster import Roaster
from src.tones import TONE_MAP, list_tones

load_dotenv()


# ── Built-in example groups (for --simulate) ────────────────────────────────

EXAMPLE_GROUPS: List[GroupPhoto] = [
    GroupPhoto(
        title="Office Team Photo",
        setting="Open-plan office, Monday morning, someone brought donuts",
        people=[
            Person(
                name="Alex",
                description="Smiling too hard, business casual with a wrinkled shirt",
                expression=Expression.SMILING,
                outfit=Outfit.CASUAL,
                vibe=Vibe.OVER_IT,
                body_language="Arms crossed, leaning back",
                arrangement=Arrangement.FRONT_CENTER,
            ),
            Person(
                name="Jordan",
                description="Dead-eyed stare, hoodie under a blazer, drinking coffee",
                expression=Expression.DEADPAN,
                outfit=Outfit.PREPPY,
                vibe=Vibe.CONFIDENT,
                body_language="One hand in pocket, slight smirk",
                arrangement=Arrangement.BACK_LEFT,
            ),
            Person(
                name="Taylor",
                description="Awkward thumbs-up, outfit screams 'I tried'",
                expression=Expression.AWKWARD,
                outfit=Outfit.MINIMALIST,
                vibe=Vibe.NERVOUS,
                body_language="Stiff posture, forced smile",
                arrangement=Arrangement.SIDE,
            ),
            Person(
                name="Morgan",
                description="Grimacing with a full coffee cup, last night's shirt",
                expression=Expression.GRIMACING,
                outfit=Outfit.GRUNGE,
                vibe=Vibe.CHAOS,
                body_language="Slouching, holding coffee like a lifeline",
                arrangement=Arrangement.BACK_RIGHT,
            ),
        ],
    ),
    GroupPhoto(
        title="Friends Night Out",
        setting="Dive bar with neon sign, someone already spilled a drink",
        people=[
            Person(
                name="Casey",
                description="Laughing with mouth open, sunglasses indoors at night",
                expression=Expression.LAUGHING,
                outfit=Outfit.BOHEMIAN,
                vibe=Vibe.MAIN_CHARACTER,
                body_language="Arm around nearest person, leaning into the frame",
                arrangement=Arrangement.FRONT_CENTER,
            ),
            Person(
                name="Riley",
                description="Smirking knowingly, leather jacket, too cool to be here",
                expression=Expression.SMIRKING,
                outfit=Outfit.CASUAL,
                vibe=Vibe.COOL,
                body_language="Hands in jacket pockets, off-angle stance",
                arrangement=Arrangement.BACK_CENTER,
            ),
            Person(
                name="Avery",
                description="Eyes half-closed, questionable fashion layering",
                expression=Expression.SURPRISED,
                outfit=Outfit.GRUNGE,
                vibe=Vibe.GOLDEN_RETRIEVER,
                body_language="Leaning in too close, big grin",
                arrangement=Arrangement.FRONT_RIGHT,
            ),
        ],
    ),
    GroupPhoto(
        title="Family Reunion (You Know Which One)",
        setting="Someone's backyard, folding chairs, distant uncle grilling",
        people=[
            Person(
                name="Mom",
                description="Forced smile, floral blouse that means business",
                expression=Expression.SMILING,
                outfit=Outfit.FORMAL,
                vibe=Vibe.OVER_IT,
                body_language="Hands clasped, standing perfectly straight",
                arrangement=Arrangement.FRONT_CENTER,
            ),
            Person(
                name="Older Sibling",
                description="Bored expression, 'too old for this' energy",
                expression=Expression.SERIOUS,
                outfit=Outfit.CASUAL,
                vibe=Vibe.BACKGROUND_CHARACTER,
                body_language="Arms crossed, weight on one leg",
                arrangement=Arrangement.BACK_LEFT,
            ),
            Person(
                name="Younger Sibling",
                description="Grimacing with peace sign, chaotic outfit layering",
                expression=Expression.GRIMACING,
                outfit=Outfit.SPORTY,
                vibe=Vibe.CHAOS,
                body_language="Bouncing on heels, half out of frame",
                arrangement=Arrangement.FRONT_LEFT,
            ),
            Person(
                name="Cousin",
                description="Awkward smile, didn't want to be in the photo",
                expression=Expression.AWKWARD,
                outfit=Outfit.MINIMALIST,
                vibe=Vibe.AWKWARD,
                body_language="Tucked behind everyone else",
                arrangement=Arrangement.CROWDED_OUT,
            ),
        ],
    ),
]


def _describe_people() -> GroupPhoto:
    """Interactive prompt: user describes the people in their photo."""
    print("")
    print("╔══════════════════════════════════════════════╗")
    print("║   Roster — Describe Your Group for Roasting  ║")
    print("╚══════════════════════════════════════════════╝")
    print("")

    title = input("Group name (e.g. 'My Friends'): ").strip()
    setting = input("Setting (e.g. 'A rooftop, sunset'): ").strip()
    print("")
    print("Now describe each person. Press Enter blank to finish.")
    print("")

    people: List[Person] = []
    i = 1

    while True:
        print(f"── Person {i} ──")
        name = input(f"  Name (or blank to stop): ").strip()
        if not name:
            if i == 1:
                print("  At least one person required. Try again.")
                continue
            break

        desc = input(f"  Description (appearance, expression, outfit): ").strip()

        # Map simple keywords to enum values (coarse but functional)
        expr_str = input(f"  Expression [{', '.join(e.value for e in Expression)}] (default: deadpan): ").strip().lower()
        outfit_str = input(f"  Outfit [{', '.join(o.value for o in Outfit)}] (default: unknown): ").strip().lower()
        vibe_str = input(f"  Vibe [{', '.join(v.value for v in Vibe)}] (default: awkward): ").strip().lower()

        # Parse enums with fallbacks
        expression = next((e for e in Expression if e.value == expr_str), Expression.DEADPAN)
        outfit = next((o for o in Outfit if o.value == outfit_str), Outfit.UNKNOWN)
        vibe = next((v for v in Vibe if v.value == vibe_str), Vibe.AWKWARD)

        person = Person(
            name=name,
            description=desc or "No description provided.",
            expression=expression,
            outfit=outfit,
            vibe=vibe,
            body_language="",
            arrangement=Arrangement.CROWDED_OUT,
        )
        people.append(person)
        i += 1

    return GroupPhoto(title=title or "My Group", setting=setting, people=people)


def _select_tone() -> str:
    """Prompt the user to pick a tone."""
    tones = list_tones()
    print("")
    print("Available roast tones:")
    print("")
    for t in tones:
        print(f"  {t.name:20s}  ({t.intensity}/10) {t.vibe}")
    print("")
    choice = input("Pick a tone: ").strip().lower()

    while choice not in TONE_MAP:
        print(f"Unknown tone '{choice}'. Try one of: {', '.join(TONE_MAP)}")
        choice = input("Pick a tone: ").strip().lower()

    return choice


def _select_tone_arg(name: str) -> str:
    """Validate a tone name from command line."""
    if name in TONE_MAP:
        return name
    print(f"Unknown tone '{name}'. Available: {', '.join(TONE_MAP)}", file=sys.stderr)
    sys.exit(1)


def cmd_roast(args: argparse.Namespace) -> None:
    """Interactive roast flow."""
    tone_name = args.tone or _select_tone()
    tone = TONE_MAP[tone_name]
    group = _describe_people()

    if not group.people:
        print("No people described. Nothing to roast.")
        sys.exit(1)

    roaster = Roaster()
    card = roaster.generate_roasts(group, tone, simulate=True)

    print("")
    print(format_card(card))
    print("")

    save = input("Save roast card to file? (y/N): ").strip().lower()
    if save == "y":
        fname = f"roast_cards/{group.title.replace(' ', '_').lower()}_{tone_name}.txt"
        format_card(card, filepath=fname)
        print(f"  Saved to {fname}")


def cmd_simulate(args: argparse.Namespace) -> None:
    """Run with built-in example groups."""
    tone_name = args.tone or "siblings"
    tone = TONE_MAP[tone_name]

    roaster = Roaster()

    for i, group in enumerate(EXAMPLE_GROUPS, 1):
        card = roaster.generate_roasts(group, tone, simulate=True)
        print(format_card(card))
        if i < len(EXAMPLE_GROUPS):
            print("\n\n" + "=" * CARD_WIDTH + "\n")


def cmd_list_tones(_args: argparse.Namespace) -> None:
    """List all available tones."""
    print("")
    print(f"{'Name':20s}  {'Intensity':>10s}  Vibe")
    print(f"{'─'*20:20s}  {'─'*10:>10s}  {'─'*40}")
    for t in list_tones():
        print(f"{t.name:20s}  {t.intensity:>3d}/10      {t.vibe}")
    print("")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Roster — AI group photo roasts. Best served cold.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--roast",
        action="store_true",
        help="Interactive mode: describe your group and get roasted",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run with built-in example groups (siblings, coworkers, friends)",
    )
    parser.add_argument(
        "--tone",
        type=str,
        default="",
        help="Roast tone name (default: siblings or interactive pick). See --list-tones",
    )
    parser.add_argument(
        "--list-tones",
        dest="list_tones",
        action="store_true",
        help="List all available roast tones",
    )

    args = parser.parse_args()

    if args.list_tones:
        cmd_list_tones(args)
    elif args.simulate:
        cmd_simulate(args)
    elif args.roast:
        cmd_roast(args)
    else:
        parser.print_help()
        print("")
        print("Quick start:")
        print("  python main.py --simulate             # See it in action")
        print("  python main.py --roast                # Describe your own group")
        print("  python main.py --list-tones            # See all roast styles")


if __name__ == "__main__":
    main()