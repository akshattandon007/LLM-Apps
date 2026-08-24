"""Verdict generation logic for HomeCourt.

Supports two modes:
  1. Simulated — generates a procedural verdict using persona templates
     (no API key needed). Great for demos and testing.
  2. Live — calls an LLM API via httpx using the persona's prompt.
"""

from __future__ import annotations

import os
import random
from datetime import date
from typing import Literal

import httpx

from src.models import Case, PersonaDef, Verdict
from src.personas import get_persona

# ── Simulated verdicts ──────────────────────────────────────────────────────

_DISSENTING_OPTIONS = [
    "One juror was overheard muttering 'I'd have ruled the other way' "
    "before being escorted out.",
    "A tiny dog on the jury panel disagrees but no one understands bark.",
    "The judge's cat gave a dissenting tail-flick. It has been noted.",
    "An anonymous text poll of 12 strangers on the internet split 7–5.",
    None,
]

# Each persona has a pool of possible simulated rulings keyed by `style`.
# We pick a random one and wrap it in their voice.

_SIMULATED_REASONING: dict[str, list[str]] = {
    "grumpy": [
        "I've seen this exact argument play out a thousand times since 1952. "
        "Side A has the common sense God gave a goose, and Side B is overthinking "
        "things like usual. In my day, we didn't have 'dilemmas' — we had "
        "problems and we solved them. Both sides have merit in the way that "
        "stale bread has merit: technically edible but nobody's thrilled.",
    ],
    "dramatic": [
        "Ladies and gentlemen of the court — and by that I mean everyone "
        "watching at home — this case has it ALL. Tears. Betrayal. A truly "
        "questionable life choice from Party B. The evidence is CLEAR. The "
        "testimony is COMPELLING. And I am READY to deliver the verdict "
        "that will be talked about for WEEKS.",
    ],
    "clinical": [
        "ANALYSIS:\n\nSide A argument: coherence score 7/10, evidence 5/10, "
        "emotional content 9/10 (deduction applied). Weighted score: 6.2.\n\n"
        "Side B argument: coherence score 8/10, evidence 6/10, emotional "
        "content 3/10 (neutral). Weighted score: 7.1.\n\n"
        "CONCLUSION: Side B presents the stronger logical case. Side A's "
        "argument relies heavily on subjective preference which, while valid "
        "as opinion, does not constitute persuasive evidence in this tribunal.",
    ],
    "serene": [
        "Like two rivers meeting at a confluence, both arguments flow from "
        "the same source: the human desire for things to be right. Side A's "
        "path is straight and clear; Side B meanders through careful "
        "consideration. Neither is wrong. But the river that reaches the sea "
        "first is the one that moves without hesitation. Side A carries the "
        "current of conviction. Let that be your lesson: conviction, not "
        "perfection, brings resolution.",
    ],
    "casual": [
        "OK so I've listened to both of you and here's the tea. Side A is "
        "coming from such a valid place — I see you, I respect you. But Side B "
        "is ACTUALLY making some really good points and I think everyone's "
        "just afraid to admit it. Here's the thing: you're both kind of right "
        "and kind of wrong, which is so on brand honestly. But someone has to "
        "win and someone has to lose — that's the game, bestie.",
    ],
    "poetic": [
        "Hark, the court hath weigh'd the pleas of both and finds a truth "
        "most curious: that neither party is entirely right nor yet entirely "
        "wrong. Side A speaks with passion's fire, Side B with reason's "
        "steady flame. Yet in the contest 'twixt the heart and mind, 'tis "
        "the heart that moves the world — though the mind must chart the "
        "course. The balance tips but doth not fall until the gavel falls.",
    ],
}

_SIMULATED_RULINGS: list[str] = [
    "Side A wins by a nose. Victory: sweet. Side B: better luck next lifetime.",
    "The court finds in favour of Side B. Side A's argument was emotionally compelling but logically bankrupt.",
    "Split decision. Side B wins the argument, but Side A wins the moral high ground.",
    "Side A is the victor — and frankly, it wasn't close.",
    "The court rules for Side B. No notes. Well, some notes. Mostly 'try harder'.",
    "Side A prevails. The court recommends ice cream for Side B.",
    "Siding with Side B. The evidence was clear, the tears were not.",
    "Both sides raise interesting points. Side A wins on vibes alone.",
    "Judgment for Side B. Let this be a lesson in the power of a well-structured argument.",
    "Side A takes it. The court is not accepting appeals at this time.",
]


def _simulate_verdict(case: Case, persona: PersonaDef) -> Verdict:
    """Generate a verdict without an LLM call."""
    style_key = persona.style.value
    reasoning_pool = _SIMULATED_REASONING.get(style_key, _SIMULATED_REASONING["casual"])
    reasoning = random.choice(reasoning_pool)

    ruling = random.choice(_SIMULATED_RULINGS)
    dissenting = random.choice(_DISSENTING_OPTIONS)

    return Verdict(
        case_name=case.title,
        presiding_judge=persona.name,
        judge_emoji=persona.emoji,
        date_issued=date.today(),
        reasoning=reasoning,
        ruling=ruling,
        dissenting_opinion=dissenting,
    )


# ── Live LLM verdict ────────────────────────────────────────────────────────

_LIVE_SYSTEM_PROMPT = (
    "You are a judge in the HomeCourt — a playful AI arbitration system. "
    "You will be given a case (two sides of a daily-life dilemma) and a "
    "judge persona to embody. Produce a formal verdict that includes:\n"
    "1. A brief summary of the arguments from each side\n"
    "2. Your reasoning (in the persona's voice)\n"
    "3. A clear ruling (who wins and why)\n"
    "4. Optionally, a dissenting opinion for flavour\n\n"
    "The tone must match the persona. The ruling should be quotable and "
    "shareable. Keep the response under 300 words."
)


def _build_messages(case: Case, persona: PersonaDef) -> list[dict]:
    """Build the message list for an LLM chat completion."""
    case_text = (
        f"Case: {case.title}\n\n"
        f"{case.pleas[0].side}: \"{case.pleas[0].argument}\"\n\n"
        f"{case.pleas[1].side}: \"{case.pleas[1].argument}\""
    )

    return [
        {"role": "system", "content": _LIVE_SYSTEM_PROMPT},
        {"role": "system", "content": persona.personality_prompt},
        {"role": "user", "content": f"Judge the following case:\n\n{case_text}"},
    ]


def _call_llm(messages: list[dict]) -> str:
    """Call an LLM API and return the response text."""
    api_key = os.environ.get("LLM_API_KEY")
    base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("LLM_MODEL", "gpt-4o")

    if not api_key:
        raise RuntimeError(
            "LLM_API_KEY not set. Either configure your .env file or use "
            "--simulate mode."
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.8,
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    return content.strip()


def _live_verdict(case: Case, persona: PersonaDef) -> Verdict:
    """Generate a verdict by calling the LLM API."""
    messages = _build_messages(case, persona)
    raw = _call_llm(messages)

    # Build a structured Verdict from the free-form response.
    # The LLM writes in-character; we wrap it in the formal structure.
    return Verdict(
        case_name=case.title,
        presiding_judge=persona.name,
        judge_emoji=persona.emoji,
        date_issued=date.today(),
        reasoning=raw,
        ruling="See reasoning above. The court's opinion is delivered in full.",
        dissenting_opinion=None,
        raw_response=raw,
    )


# ── Public API ──────────────────────────────────────────────────────────────


def render_verdict(
    case: Case,
    persona_key: str,
    mode: Literal["live", "simulate"] = "simulate",
) -> Verdict:
    """Render a verdict for the given case and persona.

    Parameters
    ----------
    case : Case
        The case with two pleas.
    persona_key : str
        Key of the judge persona (e.g. 'grouchy_grandma').
    mode : str
        'live' for LLM API, 'simulate' for procedural demo output.

    Returns
    -------
    Verdict
        The structured verdict.
    """
    persona = get_persona(persona_key)

    if mode == "live":
        return _live_verdict(case, persona)
    return _simulate_verdict(case, persona)