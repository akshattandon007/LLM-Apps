"""Dream interpretation engine — calls the LLM for symbolic dream analysis.

Uses the configured Hermes CLI to get structured interpretations.
Falls back to a built-in symbolic lookup if Hermes is unavailable.
"""

from __future__ import annotations

import json
import re
import subprocess
from typing import Optional

from .models import DreamInterpretation

HERMES_BIN = "/opt/venv/bin/hermes"


def interpret(dream_text: str) -> Optional[DreamInterpretation]:
    """Send dream text to the LLM and return a structured interpretation.

    Tries the live Hermes CLi first. If it fails or times out, falls back
    to a keyword-based symbolic interpreter.
    """
    if not dream_text or not dream_text.strip():
        return None

    result = _call_llm(dream_text)
    if result is not None:
        return result

    # Fallback: keyword-based interpretation
    return _fallback_interpret(dream_text)


def _call_llm(dream_text: str) -> Optional[DreamInterpretation]:
    """Call Hermes CLI for dream interpretation.

    Constructs a system prompt asking for structured JSON output.
    """
    prompt = (
        "You are a dream interpreter trained in Jungian, Freudian, and modern dream psychology. "
        "Analyze the following dream description and return ONLY a valid JSON object "
        "with these exact keys:\n"
        '  - "interpretation": string (2-3 paragraphs of insightful analysis)\n'
        '  - "symbols": array of strings (key symbols identified)\n'
        '  - "mood": string (overall mood/tone, one or two words)\n'
        '  - "themes": array of strings (recurring themes or motifs)\n\n'
        f"Dream: {dream_text}\n\n"
        "Return ONLY valid JSON. No markdown, no code fences, no extra text."
    )

    try:
        proc = subprocess.run(
            [HERMES_BIN, "chat", "-p", "chief", "-q", prompt],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode != 0:
            return None

        output = proc.stdout.strip()
        return _parse_json_response(output)

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def _parse_json_response(raw: str) -> Optional[DreamInterpretation]:
    """Extract JSON from the LLM response, tolerating extra text or fences."""
    # Remove markdown code fences if present
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
    # Try to find a JSON object
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return None

    return DreamInterpretation(
        interpretation=data.get("interpretation", raw[:500]),
        symbols=data.get("symbols", []),
        mood=data.get("mood", "unknown"),
        themes=data.get("themes", []),
    )


# ── Fallback keyword-based interpreter ─────────────────────────────────────

SYMBOL_LIBRARY: dict[str, dict] = {
    "flying": {
        "meaning": "Often represents freedom, escape from constraints, or a desire to transcend limitations. May also indicate a perspective shift or spiritual aspiration.",
        "mood": "liberating",
        "themes": ["freedom", "transcendence", "ambition"],
    },
    "water": {
        "meaning": "Symbolises the subconscious, emotions, and the flow of life. Still water suggests peace; rough water indicates emotional turbulence.",
        "mood": "fluid",
        "themes": ["emotion", "subconscious", "change"],
    },
    "falling": {
        "meaning": "Often reflects a fear of losing control, failure, or letting go. Can also represent surrender to natural forces or release from anxiety.",
        "mood": "anxious",
        "themes": ["loss of control", "fear", "surrender"],
    },
    "darkness": {
        "meaning": "Represents the unknown, the unconscious, or aspects of self we haven't confronted. Not necessarily negative — can signal depth and potential.",
        "mood": "mysterious",
        "themes": ["unknown", "introspection", "potential"],
    },
    "light": {
        "meaning": "Illumination, clarity, hope, or spiritual awakening. Often appears in dreams about insight, resolution, or breakthrough moments.",
        "mood": "hopeful",
        "themes": ["clarity", "hope", "revelation"],
    },
    "door": {
        "meaning": "A threshold or transition point. Open doors invite new opportunities; closed doors may represent missed chances or choices yet to be made.",
        "mood": "anticipatory",
        "themes": ["transition", "opportunity", "choice"],
    },
    "mirror": {
        "meaning": "Self-reflection, identity, and how you perceive yourself. May indicate a period of self-examination or confronting your own image.",
        "mood": "introspective",
        "themes": ["identity", "self-reflection", "truth"],
    },
    "animal": {
        "meaning": "Instinct, primal energy, or untamed aspects of personality. Specific animals carry additional symbolism (wolf = loyalty, snake = transformation).",
        "mood": "wild",
        "themes": ["instinct", "nature", "primal self"],
    },
    "garden": {
        "meaning": "The mind's cultivated space — growth, nurturing, and what you choose to develop in your life. Overgrown gardens suggest neglected potential.",
        "mood": "peaceful",
        "themes": ["growth", "nurturing", "potential"],
    },
    "storm": {
        "meaning": "Conflict, upheaval, or intense emotion. Storms can be cleansing or destructive — often both. May indicate a period of necessary change.",
        "mood": "turbulent",
        "themes": ["conflict", "change", "catharsis"],
    },
    "mountain": {
        "meaning": "A challenge to overcome, an ambitious goal, or a spiritual ascent. The climb represents effort; the summit represents achievement or perspective.",
        "mood": "determined",
        "themes": ["challenge", "achievement", "perspective"],
    },
    "clock": {
        "meaning": "Time pressure, mortality awareness, or the sense that a deadline is approaching. Broken clocks suggest feeling stuck or disconnected from time.",
        "mood": "urgent",
        "themes": ["time", "mortality", "pressure"],
    },
}

# Common mood modifiers
MOOD_KEYWORDS: dict[str, str] = {
    "scared": "fearful",
    "happy": "joyful",
    "sad": "melancholic",
    "confused": "bewildered",
    "angry": "furious",
    "calm": "serene",
    "excited": "elated",
    "peaceful": "serene",
    "strange": "surreal",
    "beautiful": "wondrous",
}


def _fallback_interpret(dream_text: str) -> DreamInterpretation:
    """Simple keyword-based interpretation when LLM is unavailable."""
    text_lower = dream_text.lower()
    found_symbols: list[str] = []
    found_themes: set[str] = set()
    mood_votes: dict[str, int] = {}

    for keyword, data in SYMBOL_LIBRARY.items():
        if keyword in text_lower:
            found_symbols.append(keyword)
            found_themes.update(data["themes"])
            m = data["mood"]
            mood_votes[m] = mood_votes.get(m, 0) + 1

    # Also check for mood keywords in the text
    for kw, mood in MOOD_KEYWORDS.items():
        if kw in text_lower:
            mood_votes[mood] = mood_votes.get(mood, 0) + 1

    if not found_symbols:
        found_symbols = ["unknown"]
        mood_votes.setdefault("mysterious", 1)
        found_themes.add("unclear")

    # Determine dominant mood
    dominant_mood = max(mood_votes, key=mood_votes.get) if mood_votes else "unknown"

    # Build interpretation paragraphs
    symbols_analysis = "; ".join(
        f"{s}: {SYMBOL_LIBRARY.get(s, {}).get('meaning', 'Symbolic meaning unclear.')}"
        for s in found_symbols if s in SYMBOL_LIBRARY
    )
    if not symbols_analysis:
        symbols_analysis = f"The dream contains imagery that doesn't match common dream symbols. Consider what '{dream_text[:50]}...' means to you personally."

    interpretation = (
        f"This dream features prominent {', '.join(found_symbols)} imagery. "
        f"{symbols_analysis} "
        f"The overall mood appears {dominant_mood}. "
        f"Themes detected include: {', '.join(sorted(found_themes))}. "
        "For a deeper analysis, ensure the Hermes LLM is configured and available."
    )

    return DreamInterpretation(
        interpretation=interpretation,
        symbols=found_symbols,
        mood=dominant_mood,
        themes=sorted(found_themes),
    )