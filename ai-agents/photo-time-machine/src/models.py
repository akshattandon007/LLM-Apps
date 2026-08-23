from __future__ import annotations

from pydantic import BaseModel, Field


class EraStyle(BaseModel):
    """Describes a single historical-era style transformation."""

    decade: str = Field(..., min_length=1, description="Decade label, e.g. '1950s'")
    title: str = Field(..., min_length=1, description="Human-readable title for the era card")
    style_description: str = Field(
        ..., min_length=1, description="What the person would look like in this era"
    )
    visual_filter: str = Field(
        ..., min_length=1, description="Simulated photo filter effect description"
    )
    caption: str = Field(
        ..., min_length=1, description="Short playful one-liner about this era version"
    )
    tagline: str = Field(..., min_length=1, description="Fun tagline for the era card")
    accent_colors: list[str] = Field(
        ..., min_length=2, description="Two or three hex colour codes representative of the era"
    )


class EraTransformation(BaseModel):
    """The result of transforming a photo through one era."""

    era: str = Field(..., min_length=1, description="Decade label")
    title: str = Field(..., min_length=1)
    description: str = Field(
        ..., description="What the transformed photo would show"
    )
    caption: str = Field(...)
    tagline: str = Field(...)
    output_image: str | None = Field(
        None, description="Path to the generated image, if real gen was used"
    )


class PhotoTimeMachineOutput(BaseModel):
    """Full output from a Photo Time Machine run."""

    original_name: str = Field(..., description="Original photo filename")
    eras: list[EraTransformation] = Field(
        ..., min_length=1, description="All era transformations"
    )
    gallery_message: str = Field(
        ..., description="Summary / share text for the whole gallery"
    )