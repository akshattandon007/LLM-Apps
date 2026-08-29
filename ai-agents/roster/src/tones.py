"""Roast tone definitions — each tone is data, not logic."""

from __future__ import annotations

from typing import List
from src.models import Tone


# ── Built-in tones ──────────────────────────────────────────────────────────

SIBLINGS = Tone(
    name="siblings",
    description=(
        "Playful, affectionate roasting with 'you're adopted' energy. "
        "The kind of burns that only work because you love each other."
    ),
    vibe="Affectionate cruelty — the higher the love, the sharper the jab",
    example_phrases=[
        "Mom always liked me best and we both know it.",
        "You're not ugly, you're just… a family face.",
        "That outfit says 'I gave up' and the photo confirms it.",
        "You stood in the back to hide your height and it didn't work.",
        "At least one of us is the favourite. Spoiler: not you.",
    ],
    intensity=4,
)

COWORKERS = Tone(
    name="coworkers",
    description=(
        "Polite but cutting. 'This meeting could've been an email' energy. "
        "Professional enough to share on LinkedIn, savage enough to enjoy."
    ),
    vibe="HR-approved savagery",
    example_phrases=[
        "You bring that same energy to stand-ups and we all feel it.",
        "That smile says 'I'm fine' but your inbox says otherwise.",
        "You dressed for the job you want — a nap.",
        "The group chat coordinator energy is loud.",
        "You're the reason the slide deck has an appendix.",
    ],
    intensity=5,
)

OLD_FRIENDS = Tone(
    name="old_friends",
    description=(
        "Nostalgic, inside-joke heavy roasting. "
        "'Remember when you…' energy. Only hurts because the memory is real."
    ),
    vibe="Warm nostalgia with a shiv",
    example_phrases=[
        "Remember when you swore that haircut was cool? The photo says otherwise.",
        "You haven't changed a bit — same questionable life choices.",
        "You're still making that face. It's been ten years.",
        "We keep you around for the group chat receipts.",
        "That pose is a cry for help and we're here for it.",
    ],
    intensity=6,
)

MERCILESS = Tone(
    name="merciless",
    description=(
        "Brutal, no holds barred. 'Read for filth' energy. "
        "This is the tone you use when nobody's feelings are safe."
    ),
    vibe="Zero survivors",
    example_phrases=[
        "You look like the 'before' picture of a life coach ad.",
        "That outfit is a hate crime and the victim is everyone looking at it.",
        "You're not 'quirky', you're a warning label.",
        "Your vibe is 'ask for the manager' but you don't have the confidence to do it.",
        "If awkwardness were a superpower, you'd be the Avengers.",
    ],
    intensity=10,
)

# ── Bonus tone ──────────────────────────────────────────────────────────────

SELF_DEPRECATING = Tone(
    name="self_deprecating",
    description=(
        "A group roast where everyone joins in on themselves. "
        "Mutual destruction with a laugh."
    ),
    vibe="Roast yourself before someone else does",
    example_phrases=[
        "I'm the one who suggested this photo, which tells you everything.",
        "My posture alone is a cry for ergonomic intervention.",
        "I dressed for 'nobody's looking at me' and I was wrong.",
        "My smile is 30% joy and 70% 'please end this'.",
        "I'm the group's designated photographer because I look worse in photos.",
    ],
    intensity=3,
)

# ── Registry ────────────────────────────────────────────────────────────────

BUILTIN_TONES: List[Tone] = [
    SIBLINGS,
    COWORKERS,
    OLD_FRIENDS,
    MERCILESS,
    SELF_DEPRECATING,
]

TONE_MAP = {tone.name: tone for tone in BUILTIN_TONES}


def get_tone(name: str) -> Tone:
    """Look up a tone by name. Raises KeyError if not found."""
    if name in TONE_MAP:
        return TONE_MAP[name]
    raise KeyError(f"Unknown tone '{name}'. Available: {list(TONE_MAP)}")


def list_tones() -> List[Tone]:
    """Return all built-in tones."""
    return BUILTIN_TONES