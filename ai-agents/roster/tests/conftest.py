"""Test fixtures with mock group descriptions."""

from __future__ import annotations

import pytest

from src.models import (
    Arrangement,
    Expression,
    GroupPhoto,
    Outfit,
    Person,
    Vibe,
)
from src.tones import TONE_MAP


@pytest.fixture
def family_group() -> GroupPhoto:
    """A family reunion-style group photo."""
    return GroupPhoto(
        title="The Family Portrait",
        setting="Someone's backyard with folding chairs",
        people=[
            Person(
                name="Mom",
                description="Forced smile, floral dress, hands clasped",
                expression=Expression.SMILING,
                outfit=Outfit.FORMAL,
                vibe=Vibe.OVER_IT,
                body_language="Standing perfectly straight",
                arrangement=Arrangement.FRONT_CENTER,
            ),
            Person(
                name="Dad",
                description="Grumpy, arms crossed, 'get this over with' look",
                expression=Expression.SERIOUS,
                outfit=Outfit.CASUAL,
                vibe=Vibe.CONFIDENT,
                body_language="Arms crossed, weight on one foot",
                arrangement=Arrangement.FRONT_LEFT,
            ),
            Person(
                name="Teenager",
                description="Dead-eyed stare, hoodie, looking away from camera",
                expression=Expression.DEADPAN,
                outfit=Outfit.GRUNGE,
                vibe=Vibe.AWKWARD,
                body_language="Hands in pockets, staring at ground",
                arrangement=Arrangement.BACK_CENTER,
            ),
        ],
    )


@pytest.fixture
def coworkers_group() -> GroupPhoto:
    """An office team photo."""
    return GroupPhoto(
        title="Q3 Team Photo",
        setting="Open office, someone brought bagels",
        people=[
            Person(
                name="Manager",
                description="Big fake smile, business casual, standing front and centre",
                expression=Expression.SMILING,
                outfit=Outfit.FORMAL,
                vibe=Vibe.MAIN_CHARACTER,
                body_language="Hands behind back, chest out",
                arrangement=Arrangement.FRONT_CENTER,
            ),
            Person(
                name="Intern",
                description="Over-eager thumbs-up, too much energy",
                expression=Expression.SMIRKING,
                outfit=Outfit.CASUAL,
                vibe=Vibe.GOLDEN_RETRIEVER,
                body_language="Leaning in, big grin",
                arrangement=Arrangement.FRONT_RIGHT,
            ),
            Person(
                name="Veteran",
                description="Dead-eyed stare, hoodie under blazer, coffee cup visible",
                expression=Expression.GRIMACING,
                outfit=Outfit.PREPPY,
                vibe=Vibe.OVER_IT,
                body_language="Slouching, holding coffee like a lifeline",
                arrangement=Arrangement.BACK_LEFT,
            ),
        ],
    )


@pytest.fixture
def all_tones():
    """All available tone objects."""
    return list(TONE_MAP.values())