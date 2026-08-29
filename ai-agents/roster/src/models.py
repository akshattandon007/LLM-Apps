"""Pydantic models for Roster."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class Expression(str, Enum):
    """Detected facial expressions."""

    SMILING = "smiling"
    SERIOUS = "serious"
    SMIRKING = "smirking"
    GRIMACING = "grimacing"
    LAUGHING = "laughing"
    DEADPAN = "deadpan"
    SURPRISED = "surprised"
    AWKWARD = "awkward"


class Outfit(str, Enum):
    """Detected outfit types."""

    CASUAL = "casual"
    FORMAL = "formal"
    SPORTY = "sporty"
    BOHEMIAN = "bohemian"
    PREPPY = "preppy"
    GRUNGE = "grunge"
    MINIMALIST = "minimalist"
    UNKNOWN = "unknown"


class Vibe(str, Enum):
    """Overall vibe of a person."""

    CONFIDENT = "confident"
    AWKWARD = "awkward"
    COOL = "cool"
    NERVOUS = "nervous"
    OVER_IT = "over it"
    CHAOS = "chaos"
    GOLDEN_RETRIEVER = "golden retriever energy"
    MAIN_CHARACTER = "main character energy"
    BACKGROUND_CHARACTER = "background character"


class Arrangement(str, Enum):
    """Position in the photo arrangement."""

    FRONT_CENTER = "front center"
    FRONT_LEFT = "front left"
    FRONT_RIGHT = "front right"
    BACK_CENTER = "back center"
    BACK_LEFT = "back left"
    BACK_RIGHT = "back right"
    SIDE = "side"
    CROWDED_OUT = "crowded out"


class RoastTarget(str, Enum):
    """What the roast targets."""

    EXPRESSION = "expression"
    OUTFIT = "outfit"
    VIBE = "vibe"
    BODY_LANGUAGE = "body language"
    ARRANGEMENT = "arrangement"


class Tone(BaseModel):
    """A roast tone definition."""

    name: str
    description: str
    vibe: str
    example_phrases: List[str] = Field(default_factory=list)
    intensity: int = Field(ge=1, le=10)


class Person(BaseModel):
    """A person detected/simulated in a group photo."""

    name: str = ""
    description: str
    expression: Expression = Expression.DEADPAN
    outfit: Outfit = Outfit.UNKNOWN
    vibe: Vibe = Vibe.AWKWARD
    body_language: str = ""
    arrangement: Arrangement = Arrangement.CROWDED_OUT


class Roast(BaseModel):
    """A single person's roast."""

    person: Person
    tone: str
    targets: List[RoastTarget]
    lines: List[str] = Field(default_factory=list)
    insult: str = ""
    final_verdict: str = ""


class GroupPhoto(BaseModel):
    """A group photo with detected people."""

    title: str = "Untitled Group"
    people: List[Person] = Field(default_factory=list)
    setting: str = ""
    total_count: int = 0


class RoastCard(BaseModel):
    """The final shareable roast card output."""

    title: str
    tone: Tone
    group: GroupPhoto
    roasts: List[Roast] = Field(default_factory=list)
    group_roast: str = ""
    footer: str = ""