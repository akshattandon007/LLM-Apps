from __future__ import annotations

from src.models import EraStyle

# ── Era definitions ──────────────────────────────────────────────────────────
# Each era describes a decade's style, visual filter, caption, tagline, and
# accent colours.  These drive the simulated transformations in transformer.py.

ERAS: list[EraStyle] = [
    EraStyle(
        decade="1950s",
        title="1950s — Rock Around the Clock",
        style_description=(
            "Poodle skirts, leather jackets, slicked-back greaser hair, "
            "cat-eye glasses, and saddle shoes."
        ),
        visual_filter=(
            "Black-and-white film grain with soft vignette and high contrast, "
            "like a classic Hollywood portrait."
        ),
        caption="You've been transported to the sock hop!",
        tagline="Rock around the clock",
        accent_colors=["#2a2a2a", "#e8e8e8", "#c0c0c0"],
    ),
    EraStyle(
        decade="1970s",
        title="1970s — Stayin' Alive",
        style_description=(
            "Bell-bottom jeans, patterned polyester shirts, huge afros or "
            "feathered hair, platform shoes, and peace-sign accessories."
        ),
        visual_filter=(
            "Warm sepia-toned film with soft glow and light bloom, evoking "
            "a sun-soaked disco floor."
        ),
        caption="Disco never dies — and neither does your style!",
        tagline="Stayin' Alive",
        accent_colors=["#d4a373", "#8b5e3c", "#f4d03f"],
    ),
    EraStyle(
        decade="1990s",
        title="1990s — Smells Like Teen Spirit",
        style_description=(
            "Frosted tips, flannel shirts layered over band tees, ripped "
            "jeans, chokers, scrunchies, and combat boots."
        ),
        visual_filter=(
            "Cool-blue desaturated tint with slight grain and a faded "
            "polaroid border, like a 90s yearbook photo."
        ),
        caption="As if! You're totally 90s now.",
        tagline="Smells Like Teen Spirit",
        accent_colors=["#6b8e9b", "#3d5a80", "#a8c0c8"],
    ),
    EraStyle(
        decade="2000s",
        title="2000s — Bye Bye Bye",
        style_description=(
            "Low-rise jeans, frosted lip gloss and eyeshadow, butterfly "
            "clips, trucker hats, and chunky platform sneakers."
        ),
        visual_filter=(
            "Bright blown-out digital camera flash with high saturation and "
            "slight chromatic aberration — pure 2000s digicam energy."
        ),
        caption="You look like you just stepped out of a music video!",
        tagline="Bye Bye Bye",
        accent_colors=["#e84a7a", "#f9d342", "#b5d6e0"],
    ),
    EraStyle(
        decade="2025",
        title="2025 — As You Are Today",
        style_description=(
            "Your natural look — clean, minimal aesthetic with whatever "
            "style you're rocking right now."
        ),
        visual_filter=(
            "True-to-life natural colour with balanced lighting and sharp "
            "detail — no gimmicks, just you."
        ),
        caption="Present-day you. Perfect as is.",
        tagline="As you are today",
        accent_colors=["#4a7c59", "#f5f5f5", "#2c3e50"],
    ),
    EraStyle(
        decade="2050s",
        title="2050s — Beyond 2025",
        style_description=(
            "Neon-trimmed cyberpunk attire, holographic makeup, metallic "
            "fabrics, augmented-reality glasses, and glowing hair accents."
        ),
        visual_filter=(
            "Electric neon glow with deep shadows, cyan-magenta split tone, "
            "and subtle light trails — straight out of a sci-fi film."
        ),
        caption="The future looks incredible on you.",
        tagline="Beyond 2025",
        accent_colors=["#00f0ff", "#ff00e4", "#120458"],
    ),
]


def get_era_by_decade(decade: str) -> EraStyle | None:
    """Look up an era by its decade label."""
    for era in ERAS:
        if era.decade == decade:
            return era
    return None


def all_eras() -> list[EraStyle]:
    """Return all era definitions."""
    return list(ERAS)