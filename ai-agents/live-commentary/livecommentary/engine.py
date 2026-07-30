"""Turning match events into spoken commentary, in any language.

Two engines, one interface:

* :class:`ClaudeEngine` — uses Anthropic's API to write natural, context-aware
  commentary directly in the requested language. This is what makes the output
  feel like a real broadcaster rather than a templated readout.
* :class:`TemplateEngine` — a dependency-free, offline fallback. It still
  produces reasonable commentary (and a few canned translations) so the project
  runs with zero setup and the tests need no network.

Both take a :class:`MatchState`, the new :class:`MatchEvent`, and a short list
of recent lines (for continuity / anti-repetition), and return one short burst
of commentary.
"""

from __future__ import annotations

from typing import List, Optional, Protocol

from .models import EventType, MatchEvent, MatchState
from .styles import style_instruction


class CommentaryEngine(Protocol):
    language: str

    def commentate(
        self, state: MatchState, event: MatchEvent, history: List[str]
    ) -> str: ...


# --------------------------------------------------------------------------- #
# Claude-backed engine
# --------------------------------------------------------------------------- #
class ClaudeEngine:
    """Generates commentary with the Anthropic API in the target language."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-haiku-latest",
        language: str = "English",
        style: str = "play-by-play",
        max_tokens: int = 160,
    ):
        import anthropic  # lazy: only required when actually using Claude

        self.client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        self.model = model
        self.language = language
        self.style = style
        self.max_tokens = max_tokens

    def _system(self) -> str:
        return (
            f"{style_instruction(self.style)}\n\n"
            f"Write ALL commentary in {self.language}. Use natural, idiomatic "
            f"{self.language} as a native broadcaster would — do not translate "
            f"word-for-word from English. Keep each turn to 1-2 punchy sentences. "
            f"Do not repeat lines you have already said. Do not add stage "
            f"directions, quotation marks, or speaker labels — output only the "
            f"words to be spoken."
        )

    def commentate(
        self, state: MatchState, event: MatchEvent, history: List[str]
    ) -> str:
        recent = "\n".join(f"- {h}" for h in history[-4:]) or "(none yet)"
        user = (
            f"Match: {state.home.name} vs {state.away.name} "
            f"({state.league}).\n"
            f"Current score: {state.scoreline()}. Clock: {state.clock or 'pre-match'}.\n"
            f"Your last lines:\n{recent}\n\n"
            f"NEW EVENT ({event.type}, {event.clock or '—'}): {event.text}\n\n"
            f"Commentate on this new event now, continuing naturally from your "
            f"last lines."
        )
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self._system(),
            messages=[{"role": "user", "content": user}],
        )
        return "".join(
            block.text for block in msg.content if getattr(block, "type", "") == "text"
        ).strip()


# --------------------------------------------------------------------------- #
# Offline template engine
# --------------------------------------------------------------------------- #
# A tiny multilingual phrasebook so the offline demo is genuinely multilingual.
_PHRASES = {
    "English": {
        EventType.GOAL: "GOAL! {text}",
        EventType.PENALTY: "It's a penalty! {text}",
        EventType.CARD: "Into the book — {text}",
        EventType.SAVE: "Brilliant save! {text}",
        EventType.SUBSTITUTION: "A change is made. {text}",
        EventType.KICKOFF: "And we're underway! {text}",
        EventType.FULL_TIME: "That's the final whistle. {text}",
        "_default": "{text}",
        "_score": "It's {home} {hs}, {away} {as_}.",
    },
    "Spanish": {
        EventType.GOAL: "¡GOOOL! {text}",
        EventType.PENALTY: "¡Es penalti! {text}",
        EventType.CARD: "Tarjeta — {text}",
        EventType.SAVE: "¡Gran parada! {text}",
        EventType.SUBSTITUTION: "Hay cambio. {text}",
        EventType.KICKOFF: "¡Comienza el partido! {text}",
        EventType.FULL_TIME: "Final del encuentro. {text}",
        "_default": "{text}",
        "_score": "El marcador: {home} {hs}, {away} {as_}.",
    },
    "French": {
        EventType.GOAL: "BUUUT ! {text}",
        EventType.PENALTY: "Penalty ! {text}",
        EventType.CARD: "Carton — {text}",
        EventType.SAVE: "Quel arrêt ! {text}",
        EventType.SUBSTITUTION: "Changement. {text}",
        EventType.KICKOFF: "Le match est lancé ! {text}",
        EventType.FULL_TIME: "Coup de sifflet final. {text}",
        "_default": "{text}",
        "_score": "Le score : {home} {hs}, {away} {as_}.",
    },
}


class TemplateEngine:
    """Rule-based, offline engine. No network, no keys, fully deterministic."""

    def __init__(self, language: str = "English", style: str = "play-by-play"):
        self.language = language
        self.style = style

    def commentate(
        self, state: MatchState, event: MatchEvent, history: List[str]
    ) -> str:
        book = _PHRASES.get(self.language, _PHRASES["English"])
        template = book.get(event.type, book["_default"])
        # Avoid doubling a cue the source text already opens with (e.g. "GOAL!").
        cue = template.split("{text}")[0].strip()
        text = event.text
        if cue and text[: len(cue)].lower().startswith(cue.split()[0].lower()):
            line = text
        else:
            line = template.format(text=text)
        if event.is_scoring():
            line += " " + book["_score"].format(
                home=state.home.label(),
                away=state.away.label(),
                hs=state.home_score,
                as_=state.away_score,
            )
        return line
