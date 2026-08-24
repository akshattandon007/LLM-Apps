"""Pydantic models for HomeCourt."""

from datetime import date
from enum import Enum
from pydantic import BaseModel, Field


class JudgePersona(str, Enum):
    """Available judge personas."""
    GROUCHY_GRANDMA = "grouchy_grandma"
    REALITY_TV_JUDGE = "reality_tv_judge"
    STRICT_LOGIC_AI = "strict_logic_ai"
    ZEN_MASTER = "zen_master"
    BEST_FRIEND = "best_friend"
    SHAKESPEAREAN = "shakespearean"


class VerdictStyle(str, Enum):
    """Style of the verdict output."""
    GRUMPY = "grumpy"
    DRAMATIC = "dramatic"
    CLINICAL = "clinical"
    SERENE = "serene"
    CASUAL = "casual"
    POETIC = "poetic"


class CasePlea(BaseModel):
    """One side's argument in the case."""
    side: str = Field(description="Label for this side, e.g. 'Side A' or 'Party 1'")
    argument: str = Field(description="The full text of this side's plea")


class Case(BaseModel):
    """A case to be judged by HomeCourt."""
    title: str = Field(description="Short case name, e.g. 'Sushi vs Pizza'")
    pleas: list[CasePlea] = Field(
        default_factory=list,
        description="The two (or more) sides' arguments",
        min_length=2,
        max_length=2,
    )


class PersonaDef(BaseModel):
    """Definition of a judge persona."""
    key: JudgePersona
    name: str
    emoji: str
    tone: str
    style: VerdictStyle
    greeting: str
    sign_off: str
    personality_prompt: str = Field(
        description="System prompt fragment injected to shape LLM behaviour"
    )


class Verdict(BaseModel):
    """The full verdict output from a court session."""
    case_name: str
    presiding_judge: str
    judge_emoji: str
    date_issued: date
    reasoning: str = Field(description="The body of the verdict reasoning")
    ruling: str = Field(description="The final ruling — who won and what happens")
    dissenting_opinion: str | None = Field(
        default=None,
        description="Optional playful dissenting note",
    )
    raw_response: str | None = Field(
        default=None,
        description="Raw LLM response for debugging",
    )

    @property
    def formatted_header(self) -> str:
        """Return the formal header block."""
        return (
            "╔══════════════════════════════════════════════╗\n"
            "║          HOMECOURT — OFFICIAL VERDICT        ║\n"
            "╚══════════════════════════════════════════════╝"
        )

    @property
    def formatted_ruling(self) -> str:
        """Return the ruling banner."""
        return (
            "═" * 46 + "\n"
            f"  RULING: {self.ruling}\n" +
            "═" * 46
        )