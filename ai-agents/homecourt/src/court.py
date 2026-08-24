"""Main court session flow for HomeCourt."""

from __future__ import annotations

import random

from src.jurors import render_verdict
from src.models import Case, CasePlea, Verdict
from src.personas import PERSONAS, get_persona
from src.reporter import format_verdict


def run_interactive_session() -> Verdict:
    """Run an interactive court session via stdin prompts.

    Flow:
      1. Collect the case title
      2. Collect Side A's plea
      3. Collect Side B's plea
      4. Let user choose a judge persona
      5. Generate and display the verdict
    """
    print("\n⚖️  WELCOME TO HOMECOURT ⚖️")
    print("─" * 46)
    print("Settle your daily-life dilemmas with a formal (playful) verdict.\n")

    # ── Case info ────────────────────────────────────────────────────────
    title = _prompt("Case name (e.g. 'Sushi vs Pizza')", default="The Great Debate")
    side_a_label = _prompt("Side A name", default="Party 1")
    side_a_arg = _prompt(f"{side_a_label}'s argument", multiline=True)
    side_b_label = _prompt("Side B name", default="Party 2")
    side_b_arg = _prompt(f"{side_b_label}'s argument", multiline=True)

    case = Case(
        title=title,
        pleas=[
            CasePlea(side=side_a_label, argument=side_a_arg),
            CasePlea(side=side_b_label, argument=side_b_arg),
        ],
    )

    # ── Persona selection ────────────────────────────────────────────────
    print("\n🧑‍⚖️  Choose your judge persona:")
    for i, p in enumerate(PERSONAS, 1):
        print(f"  {i}. {p.emoji} {p.name} — {p.tone}")

    persona_key = _pick_persona()
    persona = get_persona(persona_key)
    print(f"\n{persona.emoji}  {persona.greeting}\n")

    # ── Generate verdict ─────────────────────────────────────────────────
    mode = _prompt(
        "Mode",
        hint="'live' (API) or 'simulate' (demo)",
        default="simulate",
    )
    mode = mode.strip().lower()
    if mode not in ("live", "simulate"):
        print("  Unknown mode. Falling back to simulate.")
        mode = "simulate"

    print("\n⚙️  The court is deliberating...\n")
    verdict = render_verdict(case, persona_key, mode=mode)  # type: ignore[unreachable] # noqa: E501

    # ── Display ──────────────────────────────────────────────────────────
    print(format_verdict(verdict))
    return verdict


def run_simulated_demo() -> Verdict:
    """Run a quick simulated demo with a random case and persona.

    Great for showing off the project without any input.
    """
    demo_cases = [
        Case(
            title="Sushi vs Pizza",
            pleas=[
                CasePlea(side="Alice", argument="Sushi is fresh, healthy, and elegant. It's the food of refined taste. Fish + rice = perfection."),
                CasePlea(side="Bob", argument="Pizza is happiness in triangle form. It's the food of the people — shareable, warm, and you can have leftovers for breakfast."),
            ],
        ),
        Case(
            title="Answer Mom's Text Now vs Tomorrow",
            pleas=[
                CasePlea(side="You Now", argument="She's your mother. She worried. A 10-second reply costs nothing. Do it now and the peace of mind is instant."),
                CasePlea(side="You Later", argument="It's a casual check-in, not an emergency. Replying now means a 47-minute conversation. Tomorrow is fine and everyone survives."),
            ],
        ),
        Case(
            title="Put Gas Now vs Get Free Coffee Then Gas",
            pleas=[
                CasePlea(side="The Responsible Adult", argument="The gauge is on empty. You will literally be stranded. Fill up first, coffee second. This is not hard."),
                CasePlea(side="The Coffee Lover", argument="The free coffee offer ends TODAY. Gas will still be there in 15 minutes. Priorities: caffeine first, combustion later."),
            ],
        ),
    ]

    case = random.choice(demo_cases)
    persona = random.choice(PERSONAS)

    print("\n⚖️  HOMECOURT — SIMULATED DEMO ⚖\n")
    print(f"  Case:     {case.title}")
    print(f"  Judge:    {persona.emoji} {persona.name}")
    print(f"\n  {persona.greeting}\n")
    print(f'  {case.pleas[0].side}: "{case.pleas[0].argument}"')
    print(f'  {case.pleas[1].side}: "{case.pleas[1].argument}"')

    verdict = render_verdict(case, persona.key.value, mode="simulate")

    print("\n⚙️  Deliberating...\n")
    print(format_verdict(verdict))
    return verdict


# ── Helpers ────────────────────────────────────────────────────────────────


def _prompt(
    label: str,
    default: str | None = None,
    multiline: bool = False,
    hint: str | None = None,
) -> str:
    """Prompt the user for input. Returns the entered value."""
    suffix = f" [{default}]" if default else ""
    hint_text = f" ({hint})" if hint else ""
    full_label = f"  {label}{hint_text}:{suffix} "

    try:
        if multiline:
            print(f"  {label} (end with a blank line):")
            lines: list[str] = []
            while True:
                line = input("  > ").strip()
                if not line:
                    break
                lines.append(line)
            value = " ".join(lines)
        else:
            value = input(full_label).strip()

        if not value and default:
            return default
        return value if value else ""
    except (EOFError, KeyboardInterrupt):
        print("\n  Court session interrupted. Goodbye!")
        raise SystemExit(0)


def _pick_persona() -> str:
    """Let the user pick a persona by number or name."""
    while True:
        try:
            choice = input("  Enter number or name: ").strip().lower()
            if not choice:
                # Random
                return random.choice(PERSONAS).key.value

            # Try number
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(PERSONAS):
                    return PERSONAS[idx].key.value

            # Try matching name or key
            for p in PERSONAS:
                if choice in (p.key.value, p.name.lower()):
                    return p.key.value

            print(f"  '{choice}' not recognised. Try a number (1–{len(PERSONAS)}) or name.")
        except (EOFError, KeyboardInterrupt):
            print("\n  Court session interrupted. Goodbye!")
            raise SystemExit(0)