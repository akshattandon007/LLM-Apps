"""Pydantic models for Artifact Explorer."""

from pydantic import BaseModel, Field
from datetime import date


class Artifact(BaseModel):
    """The core domain object — a thing that was identified."""
    name: str = Field(description="Name of the artifact")
    category: str = Field(description="Type: plant, mineral, tool, coin, book, spice, gadget, etc.")
    description: str = Field(description="Brief physical description")
    origin: str = Field(description="Geographic or cultural origin")
    era: str = Field(description="Period of origin / when it was made or first appeared")
    history: str = Field(description="How it came to be, its journey through time")
    cultural_significance: str = Field(description="Why it matters — rituals, symbolism, economic impact")
    practical_uses: str = Field(description="How it was / is used")
    fun_facts: list[str] = Field(description="Bite-sized interesting tidbits")
    briefing_date: date = Field(
        default_factory=date.today,
        alias="date",
        description="When this profile was generated",
    )


class IdentificationResult(BaseModel):
    """What the identifier returns before the historian enriches it."""
    name: str
    category: str
    description: str


class ArtifactCard(BaseModel):
    """The final formatted gallery output."""
    title: str
    body: str
    tags: list[str]