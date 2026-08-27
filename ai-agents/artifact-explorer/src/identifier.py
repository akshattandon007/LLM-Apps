"""Identify an object from a text description or image path.

MVP uses simulated identification against a built-in artifact library.
Live mode stubs the real LLM-vision path for when an API key is present.
"""

import os
import base64
from pathlib import Path
from typing import Optional

from .models import IdentificationResult

# ── Built-in artifact library (8+ artifacts for simulated mode) ──────────────

ARTIFACT_LIBRARY: dict[str, dict] = {
    "vintage camera": {
        "name": "Kodak Brownie No. 2",
        "category": "vintage camera",
        "description": "A rectangular cardboard-bodied box camera with a simple meniscus lens. Black leatherette finish, winding knob on top, waist-level viewfinder.",
    },
    "ras el hanout": {
        "name": "Ras el Hanout",
        "category": "spice blend",
        "description": "A complex North African spice blend with a warm reddish-brown hue. Contains up to 30 ingredients including cardamom, clove, cinnamon, rose petals, and dried chili.",
    },
    "egg slicer": {
        "name": "Vintage Egg Slicer",
        "category": "weird kitchen tool",
        "description": "A chrome-plated wire slicer with a hinged top. Curved bed holds the egg, thin alloy wires slice through when the lid is pressed down.",
    },
    "aloe vera": {
        "name": "Aloe Vera (Aloe barbadensis miller)",
        "category": "plant",
        "description": "A succulent with thick, fleshy green leaves edged with small white teeth. Leaves taper to a point and have a gelatinous clear inner pulp.",
    },
    "amethyst": {
        "name": "Amethyst",
        "category": "rock / mineral",
        "description": "A violet variety of quartz (SiO₂). Crystals grow as six-sided prisms terminated by pyramids. Colour ranges from pale lilac to deep purple.",
    },
    "slide rule": {
        "name": "Slide Rule (Keuffel & Esser 4081-3)",
        "category": "vintage gadget",
        "description": "A mechanical analog calculator made of bamboo and white plastic. Three logarithmic scales on a 10-inch rule with a sliding cursor and hairline.",
    },
    "roman denarius": {
        "name": "Roman Denarius (Marcus Aurelius)",
        "category": "old coin",
        "description": "A silver coin roughly 18 mm in diameter. Obverse bears a laureate bust of Marcus Aurelius; reverse shows a standing figure of Victory with palm branch.",
    },
    "folio": {
        "name": "The Anatomy of Melancholy (1638 Folio)",
        "category": "antique book",
        "description": "A calf-bound folio volume of Robert Burton's *The Anatomy of Melancholy*. Third edition, title page in red and black, engraved frontispiece, marginal annotations.",
    },
}

# ── Keywords for fuzzy matching ──────────────────────────────────────────────

KEYWORD_MAP: list[tuple[list[str], str]] = [
    (["camera", "brownie", "kodak", "photograph", "box camera"], "vintage camera"),
    (["spice", "ras el hanout", "moroccan", "north african", "cumin", "cardamom"], "ras el hanout"),
    (["slicer", "egg slicer", "kitchen", "wire cutter", "chrome"], "egg slicer"),
    (["aloe", "succulent", "plant", "gel", "leaves", "fleshy"], "aloe vera"),
    (["amethyst", "quartz", "crystal", "purple", "violet", "mineral"], "amethyst"),
    (["slide rule", "calculator", "logarithm", "ruler", "analog"], "slide rule"),
    (["coin", "denarius", "roman", "silver", "aurelius", "marcus"], "roman denarius"),
    (["book", "folio", "anatomy", "melancholy", "burton", "antique", "1638"], "folio"),
]


def _fuzzy_match(query: str) -> str:
    """Find the best matching artifact key from a free-text query."""
    q = query.lower().strip()
    for keywords, key in KEYWORD_MAP:
        if any(kw in q for kw in keywords):
            return key
    # Last-resort: match on any single word in the artifact name
    for name_key in ARTIFACT_LIBRARY:
        if any(word in q for word in name_key.lower().split()):
            return name_key
    return ""


def identify_from_text(query: str) -> Optional[IdentificationResult]:
    """Return an IdentificationResult from a text description (simulated)."""
    key = _fuzzy_match(query)
    if not key:
        return None
    data = ARTIFACT_LIBRARY[key]
    return IdentificationResult(
        name=data["name"],
        category=data["category"],
        description=data["description"],
    )


def identify_from_image(image_path: str, api_key: Optional[str] = None) -> Optional[IdentificationResult]:
    """Identify an object from an image file.

    In simulated mode (no API key), falls back to guessing based on filename.
    In live mode, sends the image to an LLM with vision for identification.

    This is a stub — live mode requires an LLM_API_KEY in .env.
    """
    if not os.path.isfile(image_path):
        return None

    path = Path(image_path)
    # Best-effort: guess from filename stem
    stem = path.stem.replace("_", " ").replace("-", " ")
    key = _fuzzy_match(stem)
    if key:
        data = ARTIFACT_LIBRARY[key]
        return IdentificationResult(
            name=data["name"],
            category=data["category"],
            description=data["description"],
        )

    # If we have a live API key, attempt real vision
    key_to_use = api_key or os.getenv("LLM_API_KEY")
    if key_to_use and key_to_use != "your-api-key-here":
        # Real vision path — for production, call an LLM vision endpoint here.
        # Stubbed for MVP: returns a generic fallback.
        return IdentificationResult(
            name=f"Unknown object ({path.name})",
            category="unknown",
            description="Photographed object — live LLM identification not yet wired in MVP.",
        )

    return None