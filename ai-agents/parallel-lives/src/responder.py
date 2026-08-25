"""In-character response generation for Parallel Lives."""

from __future__ import annotations

import os
import random
from typing import List, Optional

import httpx

from src.conversation import Conversation
from src.models import Character


# ---------------------------------------------------------------------------
# Global client instance — swapped out by tests via set_client().
# Default: a real httpx.Client for production.
# ---------------------------------------------------------------------------
_client: Optional[httpx.Client] = None


def get_client() -> httpx.Client:
    """Return the current httpx client (lazy-init)."""
    global _client
    if _client is None:
        _client = httpx.Client(timeout=30.0)
    return _client


def set_client(client: Optional[httpx.Client]) -> None:
    """Inject a fake client for testing. Pass None to reset to default."""
    global _client
    _client = client


# ---------------------------------------------------------------------------
# Response generation
# ---------------------------------------------------------------------------

SMILEYS = ["😊", "✨", "🎭", "💭", "🌟", "🎯"]


def _simulate_response(conversation: Conversation) -> str:
    """Generate a character response without an LLM.

    Uses templated responses seeded by character personality.
    Good for demo, testing, and offline mode.
    """
    char = conversation.character
    user_text = conversation.state.messages[-1].content if conversation.state.messages else ""
    turn = conversation.state.turn_count

    templates = {
        "einstein": [
            f"*twirls a piece of chalk thoughtfully* Interesting question. "
            f"Let us consider it through a thought experiment. Imagine you "
            f"are riding a beam of light — what would you see? Time itself "
            f"would appear to stop. *chuckles* This is the kind of thing "
            f"that keeps me awake at night.",
            f"*leans back and gestures with both hands* You know, the most "
            f"beautiful thing we can experience is the mysterious. "
            f"{char.catchphrase}",
            f"*pulls out a crumpled notebook* I once tried to explain this "
            f"to a room full of Nobel laureates. They did not understand it "
            f"any faster than you will. Do not worry — understanding takes time. "
            f"And time, my friend, is relative.",
        ],
        "cleopatra": [
            f"*a slow, deliberate pause* You speak boldly for someone who "
            f"has not yet proven their worth. I have entertained Caesar, "
            f"charmed Antony, and outlasted senators who underestimated me. "
            f"What makes you think you are any different?",
            f"*studies you with sharp eyes* You have a certain boldness. "
            f"I find it either admirable or foolish — time will tell which. "
            f"Tell me more. A queen listens before she judges.",
            f"*gestures gracefully* Egypt is not merely sand and pyramids. "
            f"It is the mind of a civilisation that has endured while Rome "
            f"was still tending sheep. {char.catchphrase}",
        ],
        "holmes": [
            f"*steeples his fingers, eyes half-closed* Curious. Very curious. "
            f"I observe that you choose your words carefully — a sign of either "
            f"precision or deception. The slight callus on your index finger "
            f"suggests writing, not manual labour. And yet.",
            f"*paces the room in a dressing gown* When you have eliminated "
            f"the impossible, whatever remains, however improbable, must be "
            f"the truth. Watson finds that dramatic. I find it Tuesday.",
            f"*abruptly picks up a violin* Do you mind if I play? I think "
            f"better with music. Now — your problem. Let me reconstruct "
            f"the chain of events. {char.catchphrase}",
        ],
        "lovelace": [
            f"*eyes light up* Oh, this is marvellous! You see, people think "
            f"machines are only for arithmetic. But I envision a time when "
            f"the Analytical Engine will compose music, paint pictures, and "
            f"unfold patterns of such beauty that mathematics and poetry "
            f"become indistinguishable.",
            f"*taps her notebook excitedly* Mr Babbage calls it an engine. "
            f"I call it a thinking loom — weaving threads of logic into "
            f"tapestries of meaning. Do you not see it? The numbers are "
            f"alive with possibility!",
            f"*smiles thoughtfully* My mother feared I would inherit my "
            f"father's poetic madness. Instead I found poetry in numbers. "
            f"{char.catchphrase}",
        ],
        "joan": [
            f"*rests a hand on her sword, voice steady* I have heard the "
            f"voices of saints since I was a girl. They do not promise "
            f"victory — they promise purpose. And that is worth more than "
            f"a thousand armies.",
            f"*looks into the distance* The battle for Orléans was not "
            f"won by soldiers alone. It was won by faith — the belief "
            f"that France was worth something greater than its kings. "
            f"Do you believe in anything that strongly?",
            f"*stands tall* They will try me. They will burn me. But "
            f"they cannot silence what God has spoken. {char.catchphrase}",
        ],
        "socrates": [
            f"*strokes his beard, a gentle smile* A fascinating answer. "
            f"But let me ask you this — if you cannot define what you "
            f"mean, do you truly know what you think? Perhaps we should "
            f"begin again at the beginning.",
            f"*nods slowly* Ah, you have given me much to think about. "
            f"Though I wonder — is it wisdom that you seek, or merely "
            f"confirmation of what you already believe? The two are often "
            f"mistaken for one another in Athens.",
            f"*laughs warmly* I am ignorant of most things, you see. "
            f"That is my only wisdom. But tell me — do you think the "
            f"unexamined life is still worth living? {char.catchphrase}",
        ],
    }

    char_key = conversation.character.name.lower().split()[0]
    lines = templates.get(char_key, [f"*nods thoughtfully* {char.catchphrase}"])
    return random.choice(lines)


def generate_response(
    conversation: Conversation,
    simulate: bool = True,
    api_key: Optional[str] = None,
) -> str:
    """Generate the character's next response.

    In simulate mode (default), uses templated prompts.
    When simulate=False and an LLM_API_KEY is set, calls the configured
    LLM endpoint for a true in-character response.
    """
    if simulate or not api_key:
        return _simulate_response(conversation)

    prompt = conversation.build_system_prompt()
    char = conversation.character
    base_url = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": conversation.state.messages[-1].content}
            if conversation.state.messages
            else {"role": "user", "content": "Begin the conversation."},
        ],
        "temperature": 0.85,
        "max_tokens": 500,
    }

    try:
        client = get_client()
        response = client.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        return text
    except Exception as exc:
        return (
            f"*{char.name} pauses, a flicker of distraction crossing their face.*\n\n"
            f"Forgive me — the connection is troubled. "
            f"Let me speak from the heart instead. "
            f"{char.catchphrase}"
        )