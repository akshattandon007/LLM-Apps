from __future__ import annotations

from src.eras import all_eras
from src.models import EraStyle, EraTransformation


def transform_photo(
    photo_path: str,
    *,
    simulate: bool = True,
) -> list[EraTransformation]:
    """Run a photo through all era transformations.

    Parameters
    ----------
    photo_path:
        Path to the input photo file.
    simulate:
        When *True* (MVP mode), produce text descriptions of what each era
        version would look like instead of actually manipulating pixels.

    Returns
    -------
    list[EraTransformation]
        One entry per era, in chronological order.
    """
    results: list[EraTransformation] = []

    for era in all_eras():
        if simulate:
            description = _simulate_era(era, photo_path)
        else:
            description = _not_implemented(era)

        results.append(
            EraTransformation(
                era=era.decade,
                title=era.title,
                description=description,
                caption=era.caption,
                tagline=era.tagline,
                output_image=None,
            )
        )

    return results


def _simulate_era(era: EraStyle, photo_path: str) -> str:
    """Produce a playful text description of the simulated transformation."""
    style = era.style_description
    filter_desc = era.visual_filter
    caption = era.caption

    return (
        f"[SIMULATED] {era.decade} transformation applied.\n"
        f"Styling changed to: {style}\n"
        f"Filter applied: {filter_desc}\n"
        f"Caption: {caption}"
    )


def _not_implemented(era: EraStyle) -> str:
    """Placeholder for when a real image-generation API is wired."""
    return (
        f"[REAL GEN PENDING] Real image generation for {era.decade} "
        f"requires an API key. Style: {era.style_description}"
    )